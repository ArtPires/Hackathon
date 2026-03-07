# Hackathon Implementation Plan — Embodied Traffic Inspection Agent

## 1. Objective
Build a working hackathon demo of an **Embodied Agent** that uses **Agent Skills** to inspect a camera feed, detect vehicles, identify suspicious traffic behavior, and generate a structured report.

The focus is not full autonomy or production robustness. The goal is to prove this loop clearly:

**User instruction → Agent planner → Skill selection → Vision analysis → Report**

---

## 2. Hackathon Pitch
**One-line pitch:**

> We built an agent skill system for real-world traffic inspection that can interpret a natural-language request, select reusable computer-vision skills, analyze a live or recorded camera feed, and return a clear violation report.

**Why this is strong:**
- Connects AI agents to the physical world
- Uses reusable skills instead of one-off prompting
- Demonstrates real-world utility with cameras and edge-friendly tooling
- Fits robotics / physical world / infrastructure tracks

---

## 3. Demo Scope
For the hackathon, the system should support **one main scenario** and **one optional extension**.

### Main scenario
The user asks something like:
- “Inspect this road and tell me if there are stopped vehicles.”
- “Check whether any vehicle is stopped in a restricted area.”
- “Analyze this traffic feed and report anomalies.”

The system should:
1. Read the request
2. Select the right skills
3. Capture or load video frames
4. Detect vehicles
5. Track motion across frames
6. Decide whether a vehicle is stopped
7. Produce a human-readable report

### Optional extension
Support a second scenario using the same skills, such as:
- parking lot inspection
- loading zone monitoring
- curbside occupancy detection

This helps prove **skill reusability**.

---

## 4. System Architecture
```text
User Prompt
    ↓
Agent Planner
    ↓
Skill Registry
    ↓
Selected Skills
    ├── capture_stream
    ├── sample_frames
    ├── detect_vehicles
    ├── track_objects
    ├── detect_stopped_vehicles
    └── generate_report
    ↓
Final Output + Demo UI
```

### Core idea
The agent is not doing raw vision by itself. It is orchestrating a set of reusable skills.

---

## 5. Functional Requirements
### Required
- Accept a natural-language inspection request
- Process a webcam, RTSP stream, or prerecorded video
- Detect vehicles
- Estimate whether detected vehicles are moving or stopped
- Return a concise report
- Show the chosen skill chain during execution

### Nice to have
- Draw bounding boxes on output video
- Restricted zone support via ROI polygon
- Save structured JSON report
- Lightweight web dashboard
- Multiple scene presets

---

## 6. Non-Functional Goals
- Must be demoable in under 2 minutes
- Must run reliably on a laptop
- Prefer low setup friction
- Clear logs and simple UI
- Easy fallback to prerecorded video if live camera fails

---

## 7. Recommended Hackathon Scope Control
To avoid overbuilding, do **not** try to solve all traffic violations.

### Implement only:
- vehicle detection
- motion / stopped analysis
- optional ROI filtering
- report generation

### Avoid during hackathon:
- full lane analysis
- OCR / plate recognition
- multi-camera synchronization
- advanced anomaly reasoning
- cloud deployment complexity

---

## 8. Skills Definition
Each skill should be a small, well-bounded module with a clean interface.

### 8.1 `capture_stream`
**Purpose:** Open camera/video source and yield frames.

**Inputs:**
- source path, webcam index, or RTSP URL

**Outputs:**
- frame iterator

**Responsibilities:**
- validate source
- handle reconnect or file end
- expose basic metadata (fps, width, height)

---

### 8.2 `sample_frames`
**Purpose:** Reduce computation and normalize frame flow.

**Inputs:**
- frame stream
- sample interval

**Outputs:**
- sampled frames with timestamps

**Responsibilities:**
- frame skipping
- timestamp assignment
- performance control

---

### 8.3 `detect_vehicles`
**Purpose:** Detect cars, motorcycles, buses, and trucks.

**Inputs:**
- frame

**Outputs:**
- list of detections with class, confidence, bbox

**Implementation suggestion:**
- YOLOv8n or YOLOv8s

**Classes of interest:**
- car
- motorcycle
- bus
- truck

---

### 8.4 `track_objects`
**Purpose:** Associate detections across frames.

**Inputs:**
- per-frame detections

**Outputs:**
- track IDs and trajectories

**Implementation suggestion:**
- simple centroid tracking for speed
- ByteTrack if time permits

---

### 8.5 `detect_stopped_vehicles`
**Purpose:** Decide whether tracked vehicles are effectively stopped.

**Inputs:**
- track history
- time window
- movement threshold

**Outputs:**
- stopped vehicle events

**Logic:**
A vehicle is considered stopped if its centroid displacement remains under a small threshold for a minimum time window.

---

### 8.6 `filter_by_roi` (optional but valuable)
**Purpose:** Restrict analysis to a critical area.

**Inputs:**
- detections / tracks
- ROI polygon or rectangle

**Outputs:**
- filtered detections / events

**Use case:**
Only report stopped vehicles inside a restricted zone.

---

### 8.7 `generate_report`
**Purpose:** Convert events into an operator-friendly result.

**Inputs:**
- stopped events
- timestamps
- metadata

**Outputs:**
- plain text summary
- JSON result

**Example output:**
- “2 vehicles remained stopped in the restricted area for more than 8 seconds.”

---

### 8.8 `render_overlay` (optional)
**Purpose:** Create a visual demo with boxes, IDs, and ROI overlay.

**Inputs:**
- frame
- detections / tracks / ROI / labels

**Outputs:**
- annotated frame

---

## 9. Agent Planner Design
For hackathon purposes, keep the planner simple and reliable.

### Option A — Rule-based planner
Parse the prompt and map keywords to a skill chain.

**Advantages:**
- fastest to build
- more deterministic
- less likely to fail during demo

**Example mapping:**
- if prompt contains “vehicle”, “road”, “traffic” → run traffic inspection chain
- if prompt contains “stopped”, “restricted area” → enable stopped analysis + ROI filter

### Option B — LLM planner
Use an LLM to produce a plan as JSON, then execute whitelisted skills.

**Advantages:**
- more aligned with the event theme
- more impressive conceptually

**Recommendation:**
Use a hybrid approach:
- LLM creates the plan
- backend validates and executes only allowed skills

**Suggested hackathon strategy:**
Have rule-based planning as the default and optional LLM planning as a bonus mode.

---

## 10. Data Flow
1. User enters instruction
2. Planner builds inspection plan
3. Source opens video stream
4. Frames are sampled
5. Detector finds vehicles
6. Tracker maintains object history
7. Motion analyzer flags stopped objects
8. ROI filter narrows events
9. Reporter generates final answer
10. UI shows overlays and result

---

## 11. Tech Stack Recommendation
### Core
- **Python 3.11+**
- **OpenCV** for capture, image ops, and visualization
- **Ultralytics YOLO** for vehicle detection
- **NumPy** for geometry and motion logic
- **FastAPI** for demo API
- **Uvicorn** for local server

### Optional
- **Streamlit** for extremely fast demo UI
- **ByteTrack** for stronger tracking
- **Pydantic** for structured plans and reports
- **Gradio** if you want a very quick interactive interface

### Why this stack
It is fast to implement, familiar, and works well for laptop demos.

---

## 12. Project Structure
```text
traffic-agent-hackathon/
├── README.md
├── requirements.txt
├── .env.example
├── app/
│   ├── main.py
│   ├── config.py
│   ├── planner/
│   │   ├── rule_planner.py
│   │   └── llm_planner.py
│   ├── skills/
│   │   ├── capture.py
│   │   ├── sampling.py
│   │   ├── detect.py
│   │   ├── track.py
│   │   ├── stopped.py
│   │   ├── roi.py
│   │   ├── report.py
│   │   └── render.py
│   ├── pipelines/
│   │   └── traffic_inspection.py
│   ├── schemas/
│   │   ├── plan.py
│   │   └── report.py
│   └── api/
│       └── routes.py
├── assets/
│   ├── videos/
│   └── screenshots/
├── outputs/
│   ├── reports/
│   └── videos/
└── tests/
    ├── test_planner.py
    ├── test_roi.py
    └── test_stopped.py
```

---

## 13. API Design
### POST `/inspect`
**Request**
```json
{
  "prompt": "Check whether any vehicle is stopped in the restricted area",
  "source": "assets/videos/demo_road.mp4",
  "use_roi": true
}
```

**Response**
```json
{
  "plan": [
    "capture_stream",
    "sample_frames",
    "detect_vehicles",
    "track_objects",
    "detect_stopped_vehicles",
    "filter_by_roi",
    "generate_report"
  ],
  "summary": "2 vehicles remained stopped in the restricted area.",
  "events": [
    {
      "track_id": 4,
      "start_time": 12.4,
      "end_time": 21.8,
      "duration": 9.4
    }
  ]
}
```

---

## 14. Detection and Motion Strategy
### Vehicle detection
Use YOLOv8n first for speed. Only move to a larger model if accuracy is clearly insufficient.

### Tracking
For the hackathon, you can begin with a centroid tracker:
- compute bbox center
- associate with nearest previous center
- maintain history per track

### Stop detection
For each track:
- store centroid positions over time
- compute displacement over a rolling window
- if displacement < threshold for N seconds, mark as stopped

### Suggested initial thresholds
- frame sampling: 2–5 fps
- motion threshold: 5–15 pixels depending on view
- stop duration: 5–8 seconds

These should be configurable.

---

## 15. ROI Strategy
A restricted zone makes the demo more realistic and more impressive.

### Basic approach
- define a polygon or rectangle in image coordinates
- test whether bbox center falls inside ROI
- only report stopped vehicles inside that ROI

### Benefits
- reduces false positives
- demonstrates domain knowledge
- makes results easier to explain in a pitch

---

## 16. Demo UI Options
### Best fast option: Streamlit
Show:
- prompt input
- source selector
- execution plan
- output summary
- annotated frame or video

### Alternative: FastAPI + simple HTML
Better if you want cleaner architecture and API-first design.

### Minimum viable UI
Even a terminal demo works if it prints:
- selected skills
- intermediate counts
- final report

But visual overlay is strongly recommended.

---

## 17. Demo Script for the Presentation
### Suggested live demo flow
1. Introduce the problem in one sentence
2. Show the prompt
3. Run the inspection
4. Show selected skills
5. Show annotated video/frame
6. Show final report
7. Explain why skills are reusable

### Example script
> Our system treats traffic inspection as a reusable skill chain. Instead of relying on a raw prompt, the agent selects a set of validated skills for capture, detection, tracking, stopped-vehicle analysis, and reporting. That makes the workflow more reliable and transferable to new physical-world tasks.

---

## 18. Implementation Timeline
## Phase 1 — Setup (1–2 hours)
- create repo
- create venv
- install dependencies
- test video loading
- run YOLO on sample frame

## Phase 2 — Core skills (2–4 hours)
- implement capture
- implement sampling
- implement detect_vehicles
- implement simple tracking
- implement stopped detection

## Phase 3 — Agent orchestration (1–2 hours)
- implement rule planner
- create traffic inspection pipeline
- add logging of selected skills

## Phase 4 — UI / API (1–3 hours)
- create `/inspect` endpoint or Streamlit app
- show plan and summary
- render overlays

## Phase 5 — Demo hardening (1–2 hours)
- tune thresholds
- prepare stable demo video
- test fallback paths
- prepare slides / screenshots

---

## 19. Team Role Split
If working with others, use this split:

### Person 1 — Vision / CV
- detector
- tracker
- stop logic
- overlay rendering

### Person 2 — Agent / backend
- planner
- pipeline orchestration
- API
- JSON plan and reports

### Person 3 — Demo / product
- UI
- pitch deck
- screenshots
- benchmark examples
- narrative and positioning

If solo, implement in this order:
1. detection
2. stop logic
3. planner
4. UI
5. polish

---

## 20. Minimal Viable Deliverable
By the end of the hackathon, the project should at least have:
- one working video demo
- one natural-language prompt entry point
- one visible skill chain
- one final report
- one clear explanation of why skills are better than raw prompting

---

## 21. Stretch Goals
If there is extra time, add one or more:
- LLM-generated execution plan
- scene presets (road / parking / loading zone)
- JSON export of events
- confidence scoring
- multi-camera source selector
- edge deployment notes for Jetson / Raspberry Pi

---

## 22. Evaluation Framing for Judges
Frame the project around three points:

### A. Reliability
Skills are explicit and reusable, so the agent is less likely to improvise incorrectly.

### B. Transferability
The same perception and reporting skills can be reused across traffic, parking, logistics, and infrastructure inspection.

### C. Physical-world relevance
This is not a toy chatbot task. It connects AI to a real sensor stream and a real operational workflow.

---

## 23. Risks and Mitigations
### Risk: live camera fails
**Mitigation:** Always prepare prerecorded demo videos.

### Risk: tracking unstable
**Mitigation:** Use a fixed camera angle and tune thresholds for one curated demo scene.

### Risk: detection misses vehicles
**Mitigation:** Use a clear daytime video and keep class filtering simple.

### Risk: LLM planner becomes unreliable
**Mitigation:** Fall back to a rule-based planner.

### Risk: UI breaks
**Mitigation:** Keep a terminal-only path as backup.

---

## 24. Testing Plan
### Quick tests
- detector returns vehicle detections on sample image
- tracker preserves IDs over short sequence
- stopped detection flags static objects correctly
- ROI includes only intended region
- planner selects expected skill chain for known prompts

### Demo tests
- run full flow on final demo video
- verify final summary is consistent
- verify overlay video renders without crashing

---

## 25. Suggested Milestones
### Milestone 1
YOLO detects vehicles from demo video.

### Milestone 2
Tracking + stop detection works for at least one stable scene.

### Milestone 3
Planner prints chosen skill chain.

### Milestone 4
UI or API returns final summary.

### Milestone 5
Annotated visual demo ready for judges.

---

## 26. Example Prompt Set
Use these in the demo:
- “Inspect this road and tell me if any vehicle is stopped.”
- “Check whether there are stopped vehicles in the restricted area.”
- “Analyze this traffic feed and report unusual stationary vehicles.”
- “Monitor the curbside zone and summarize violations.”

---

## 27. Example Final Output
```text
Execution plan:
1. capture_stream
2. sample_frames
3. detect_vehicles
4. track_objects
5. detect_stopped_vehicles
6. filter_by_roi
7. generate_report

Result:
2 vehicles remained stopped in the restricted area for more than 8 seconds.

Notes:
- Source: demo_road.mp4
- ROI enabled: yes
- Sample rate: 3 fps
```

---

## 28. Positioning Statement
This project should be positioned not just as a traffic demo, but as a **general skill architecture for embodied inspection agents**.

That means the same structure can later support:
- agricultural robot inspection
- parking enforcement
- warehouse safety monitoring
- infrastructure surveillance
- curbside logistics analysis

---

## 29. Future Work After the Hackathon
- better tracking with ByteTrack / DeepSORT
- broader anomaly types
- event persistence database
- real RTSP deployment
- edge optimization for Jetson / Raspberry Pi
- richer LLM planning and reasoning
- robotics integration through ROS2

---

## 30. Final Recommendation
For the hackathon, optimize for:
1. clarity
2. reliability
3. visual impact
4. reusable skills

Do not try to win by complexity alone. Win by showing a tight, credible, well-scoped system that clearly demonstrates how **Agent Skills make physical-world AI workflows more reliable and reusable**.
