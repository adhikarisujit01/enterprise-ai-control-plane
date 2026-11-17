import pandas as pd

from src.scoring import score_portfolio
from src.governance import add_governance_controls
from src.recommendations import add_recommendations
from src.operating_model import build_raci_matrix, operating_model_summary, decision_rights_text
from src.executive_brief import build_executive_brief


def _sample():
    raw = pd.read_csv("data/ai_portfolio.csv")
    return add_recommendations(add_governance_controls(score_portfolio(raw)))


def test_raci_matrix_has_one_row_per_initiative():
    df = _sample()
    raci = build_raci_matrix(df)
    assert len(raci) == len(df)
    assert {"Executive Sponsor", "Business Owner", "Technical Owner", "AI Governance"}.issubset(raci.columns)


def test_summary_counts_are_nonnegative():
    summary = operating_model_summary(_sample())
    assert all(v >= 0 for v in summary.values())


def test_decision_rights_text_present():
    row = _sample().iloc[0]
    text = decision_rights_text(row)
    assert "decision_authority" in text and text["decision_authority"]
    assert "escalation_rule" in text and text["escalation_rule"]


def test_executive_brief_contains_sections():
    brief = build_executive_brief(_sample())
    assert "# Enterprise AI Transformation Executive Brief" in brief
    assert "## Executive summary" in brief
    assert "## Recommended 90-day sequence" in brief
