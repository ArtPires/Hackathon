"""Tests for the rule-based planner."""
import pytest
from app.planner.rule_planner import RulePlanner


@pytest.fixture
def planner():
    return RulePlanner()


BASE_SKILLS = {
    "capture_stream",
    "sample_frames",
    "detect_vehicles",
    "track_objects",
    "detect_stopped_vehicles",
    "generate_report",
}


@pytest.mark.parametrize("prompt,expected_skills,expect_roi", [
    (
        "Inspect this road and tell me if any vehicle is stopped.",
        BASE_SKILLS,
        False,
    ),
    (
        "Check whether any vehicle is stopped in the restricted area.",
        BASE_SKILLS | {"filter_by_roi"},
        True,
    ),
    (
        "Analyze this traffic feed and report anomalies.",
        BASE_SKILLS,
        False,
    ),
    (
        "Monitor the curbside zone and summarize violations.",
        BASE_SKILLS | {"filter_by_roi"},
        True,
    ),
    (
        "Check the parking area for stopped vehicles.",
        BASE_SKILLS | {"filter_by_roi"},
        True,
    ),
])
def test_rule_planner_skill_chain(planner, prompt, expected_skills, expect_roi):
    plan = planner.plan(prompt)
    assert set(plan.skill_chain) == expected_skills, (
        f"Expected {expected_skills}, got {set(plan.skill_chain)} for prompt: {prompt!r}"
    )
    assert plan.use_roi == expect_roi


def test_rule_planner_chain_order(planner):
    """generate_report must always be last."""
    plan = planner.plan("Check vehicles in the restricted zone.")
    assert plan.skill_chain[-1] == "generate_report"


def test_rule_planner_roi_before_report(planner):
    """filter_by_roi must appear before generate_report."""
    plan = planner.plan("Check stopped vehicles in the area.")
    chain = plan.skill_chain
    assert "filter_by_roi" in chain
    assert chain.index("filter_by_roi") < chain.index("generate_report")


def test_rule_planner_returns_inspection_plan(planner):
    from app.schemas.plan import InspectionPlan
    plan = planner.plan("Inspect the road.")
    assert isinstance(plan, InspectionPlan)
    assert isinstance(plan.skill_chain, list)
    assert len(plan.skill_chain) >= 6
