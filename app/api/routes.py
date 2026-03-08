"""FastAPI routes for the traffic inspection agent."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.pipelines.traffic_inspection import TrafficInspectionPipeline
from app.schemas.report import InspectionResult

router = APIRouter()
_pipeline = None


def get_pipeline() -> TrafficInspectionPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = TrafficInspectionPipeline()
    return _pipeline


class InspectRequest(BaseModel):
    prompt: str
    source: str
    use_roi: bool = False
    roi_polygon: Optional[List[List[int]]] = None
    use_llm_planner: bool = False


class InspectResponse(BaseModel):
    plan: List[str]
    summary: str
    events: list
    metadata: dict = {}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/inspect", response_model=InspectResponse)
def inspect(req: InspectRequest):
    try:
        result = get_pipeline().run(
            prompt=req.prompt,
            source=req.source,
            use_roi=req.use_roi,
            roi_polygon=req.roi_polygon,
            use_llm_planner=req.use_llm_planner,
            save_report=True,
            save_video=False,
        )
        events_serializable = [e.model_dump() for e in result.events]
        meta = {k: v for k, v in result.metadata.items() if k != "last_frame"}
        return InspectResponse(
            plan=result.plan,
            summary=result.summary,
            events=events_serializable,
            metadata=meta,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
