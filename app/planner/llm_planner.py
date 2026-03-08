"""LLM-based planner: uses Claude to generate a skill execution plan."""
import json
import logging
from typing import Optional

from app.schemas.plan import InspectionPlan, ALLOWED_SKILLS
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""You are a traffic inspection agent planner. Given a user instruction,
return ONLY a JSON object (no markdown, no explanation) with exactly these two keys:
- "skill_chain": a list of skill names to execute, chosen from: {ALLOWED_SKILLS}
- "use_roi": boolean, true if the task involves a restricted zone or specific area

The skill_chain MUST always include these core skills in this order:
capture_stream, sample_frames, detect_vehicles, track_objects, detect_stopped_vehicles, generate_report

You may insert filter_by_roi before generate_report when use_roi is true.
You may insert render_overlay before generate_report if visual output is requested.

Return only valid JSON."""


class LLMPlanner:
    """
    Uses the Anthropic Claude API to produce an InspectionPlan.
    Falls back to RulePlanner on any error.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def plan(self, prompt: str) -> InspectionPlan:
        """Generate a plan using Claude. Falls back to RulePlanner on error."""
        try:
            return self._llm_plan(prompt)
        except Exception as e:
            logger.warning(f"LLM planner failed ({e}), falling back to rule planner.")
            from app.planner.rule_planner import RulePlanner
            return RulePlanner().plan(prompt)

    def _llm_plan(self, prompt: str) -> InspectionPlan:
        client = self._get_client()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)

        # Validate skill chain against whitelist
        skill_chain = [s for s in data.get("skill_chain", []) if s in ALLOWED_SKILLS]
        use_roi = bool(data.get("use_roi", False))
        use_render = "render_overlay" in skill_chain

        return InspectionPlan(skill_chain=skill_chain, use_roi=use_roi, use_render=use_render)
