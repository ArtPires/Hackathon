"""Pipeline: traffic_inspection — Orchestrates the full agent skill chain."""
import logging
import os
from typing import Optional, List, Dict, Any, Union

import cv2
import numpy as np

from app.config import settings
from app.schemas.plan import InspectionPlan
from app.schemas.report import InspectionResult, StoppedEvent
from app.skills.capture import CaptureStream
from app.skills.sampling import sample_frames
from app.skills.detect import VehicleDetector
from app.skills.track import CentroidTracker
from app.skills.stopped import StoppedVehicleDetector
from app.skills.roi import ROIFilter
from app.skills.report import ReportGenerator
from app.skills import render as render_skill

logger = logging.getLogger(__name__)


class TrafficInspectionPipeline:
    """
    Orchestrates the full traffic inspection workflow.
    Each skill step is logged so the selected plan is visible during execution.
    """

    def __init__(self):
        self.detector = VehicleDetector()
        self.tracker = CentroidTracker()
        self.stopped_detector = StoppedVehicleDetector()
        self.roi_filter = ROIFilter()
        self.reporter = ReportGenerator()

    def run(
        self,
        prompt: str,
        source: Union[str, int],
        use_roi: bool = False,
        roi_polygon: Optional[List[List[int]]] = None,
        use_llm_planner: bool = False,
        save_report: bool = True,
        save_video: bool = False,
    ) -> InspectionResult:
        """
        Execute the full inspection pipeline.

        Args:
            prompt: natural-language inspection request
            source: video file path, webcam index, or RTSP URL
            use_roi: whether to restrict analysis to an ROI
            roi_polygon: list of [x, y] polygon vertices (uses default if None)
            use_llm_planner: use Claude LLM to build plan instead of rule planner
            save_report: persist JSON report to outputs/reports/
            save_video: write annotated video to outputs/videos/

        Returns:
            InspectionResult with plan, summary, events, metadata
        """
        # --- Step 0: Build execution plan ---
        plan = self._build_plan(prompt, use_roi, use_llm_planner)
        logger.info(f"Execution plan: {plan.skill_chain}")
        print("\nExecution plan:")
        for i, skill in enumerate(plan.skill_chain, 1):
            print(f"  {i}. {skill}")
        print()

        # Reset tracker for new run
        self.tracker.reset()

        # State
        all_tracks: Dict[int, Any] = {}
        frame_shape = None
        last_annotated_frame = None
        video_writer = None

        # --- Step 1: capture_stream ---
        logger.info("[1/N] capture_stream")
        cap = CaptureStream()
        cap.open(source)
        metadata = cap.metadata
        logger.info(f"  Source opened: {metadata}")

        # --- Step 2: sample_frames + processing loop ---
        logger.info("[2/N] sample_frames + detect/track loop")
        frame_gen = sample_frames(cap.frames(), target_fps=settings.SAMPLE_FPS)

        try:
            for frame, timestamp, meta in frame_gen:
                if frame_shape is None:
                    frame_shape = frame.shape
                    if save_video:
                        video_writer = self._make_video_writer(frame_shape, meta)

                # --- detect_vehicles ---
                detections = self.detector.detect(frame)

                # --- track_objects ---
                current_tracks = self.tracker.update(detections, timestamp)
                all_tracks.update(current_tracks)

                # --- render_overlay (per frame if requested) ---
                if plan.use_render:
                    stopped_so_far = self.stopped_detector.check(
                        current_tracks,
                        settings.MOTION_THRESHOLD,
                        settings.MIN_STOP_DURATION,
                    )
                    roi_poly = roi_polygon if plan.use_roi else None
                    annotated = render_skill.annotate_frame(
                        frame, current_tracks, stopped_so_far, roi_poly
                    )
                    last_annotated_frame = annotated
                    if video_writer:
                        video_writer.write(annotated)
                else:
                    last_annotated_frame = frame

        finally:
            cap.release()
            if video_writer:
                video_writer.release()

        # --- detect_stopped_vehicles ---
        logger.info("[3/N] detect_stopped_vehicles")
        stopped_events: List[StoppedEvent] = self.stopped_detector.check(
            all_tracks,
            settings.MOTION_THRESHOLD,
            settings.MIN_STOP_DURATION,
        )
        logger.info(f"  Raw stopped events: {len(stopped_events)}")

        # --- filter_by_roi ---
        if plan.use_roi:
            logger.info("[4/N] filter_by_roi")
            poly = roi_polygon
            if poly is None and frame_shape is not None:
                poly = self.roi_filter.default_roi(frame_shape)
            stopped_events = self.roi_filter.filter_events(
                stopped_events, all_tracks, poly, frame_shape
            )
            logger.info(f"  Events after ROI filter: {len(stopped_events)}")

        # --- generate_report ---
        logger.info("[N] generate_report")
        report_meta = {
            "source": source,
            "use_roi": plan.use_roi,
            "sample_fps": settings.SAMPLE_FPS,
            "min_stop_duration": settings.MIN_STOP_DURATION,
        }
        summary, report_json = self.reporter.generate(stopped_events, report_meta)

        if save_report:
            report_path = self.reporter.save_json(report_json)
            logger.info(f"  Report saved: {report_path}")

        print(f"\nResult:\n{summary}\n")
        print(f"Notes:")
        print(f"  - Source: {source}")
        print(f"  - ROI enabled: {plan.use_roi}")
        print(f"  - Sample rate: {settings.SAMPLE_FPS} fps")

        return InspectionResult(
            plan=plan.skill_chain,
            summary=summary,
            events=stopped_events,
            metadata={
                **report_meta,
                "last_frame": last_annotated_frame,
            },
        )

    def _build_plan(self, prompt: str, use_roi: bool, use_llm: bool) -> InspectionPlan:
        if use_llm:
            from app.planner.llm_planner import LLMPlanner
            plan = LLMPlanner().plan(prompt)
        else:
            from app.planner.rule_planner import RulePlanner
            plan = RulePlanner().plan(prompt)

        # Override use_roi if explicitly requested by caller
        if use_roi and not plan.use_roi:
            plan.use_roi = True
            from app.schemas.plan import InspectionPlan
            chain = list(plan.skill_chain)
            if "filter_by_roi" not in chain:
                chain.insert(chain.index("generate_report"), "filter_by_roi")
            plan = InspectionPlan(skill_chain=chain, use_roi=True, use_render=plan.use_render)

        return plan

    def _make_video_writer(self, frame_shape, meta):
        os.makedirs("outputs/videos", exist_ok=True)
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"outputs/videos/annotated_{ts}.mp4"
        h, w = frame_shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = meta.get("fps", 25.0)
        return cv2.VideoWriter(path, fourcc, fps, (w, h))
