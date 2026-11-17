import pandas as pd

from src.scoring import score_portfolio
from src.governance import add_governance_controls
from src.recommendations import add_recommendations


def sample_df():
    return pd.DataFrame([{
        "initiative_id": "AI-001",
        "initiative_name": "Test Agent",
        "business_function": "Finance",
        "ai_type": "Agentic AI",
        "stage": "Pilot",
        "executive_owner": "CFO",
        "business_owner": "Finance Director",
        "technical_owner": "AI Platform Team",
        "revenue_uplift_eur": 500000,
        "cost_savings_eur": 300000,
        "implementation_cost_eur": 200000,
        "annual_run_cost_eur": 100000,
        "customer_impact": 70,
        "strategic_alignment": 80,
        "data_readiness": 70,
        "technology_readiness": 75,
        "organization_readiness": 60,
        "skills_readiness": 65,
        "autonomy": 85,
        "consequence_severity": 80,
        "data_sensitivity": 70,
        "regulatory_exposure": 80,
        "model_uncertainty": 55,
        "has_named_owner": True,
        "has_human_override": False,
        "has_audit_logging": True,
        "has_kill_switch": False,
    }])


def test_scores_and_governance():
    df = score_portfolio(sample_df())
    df = add_governance_controls(df)
    df = add_recommendations(df)
    row = df.iloc[0]
    assert 0 <= row.business_value_score <= 100
    assert 0 <= row.readiness_score <= 100
    assert 0 <= row.risk_score <= 100
    assert row.governance_tier == 4
    assert "Human override" in row.control_gaps
    assert "Kill switch" in row.control_gaps
    assert row.recommendation in {"SCALE NOW", "CONTROLLED PILOT", "REDESIGN", "HOLD", "STOP"}

from src.agent_registry import build_agent_registry, kill_switch_status


def test_agent_registry_has_permission_risk():
    df = score_portfolio(sample_df())
    df = add_governance_controls(df)
    reg = build_agent_registry(df)
    row = reg.iloc[0]
    assert 0 <= row.permission_risk_score <= 100
    assert row.permission_risk_band in {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    assert "provider" in reg.columns
    assert kill_switch_status(row) in {"READY", "MISSING — blocking control", "Recommended", "Not required for non-agentic system"}
