from __future__ import annotations

import pandas as pd

from src.scoring import score_portfolio
from src.governance import add_governance_controls
from src.recommendations import add_recommendations


def run_portfolio_scenario(
    base_df: pd.DataFrame,
    benefit_realization: float = 1.0,
    implementation_cost_multiplier: float = 1.0,
    run_cost_multiplier: float = 1.0,
    readiness_uplift: float = 0.0,
    autonomy_delta: float = 0.0,
    uncertainty_delta: float = 0.0,
) -> pd.DataFrame:
    """Re-score a portfolio under explicit executive scenario assumptions.

    Multipliers are expressed as decimals (1.0 = baseline). Uplifts/deltas are
    percentage-point changes on the original 0-100 input scales.
    """
    out = base_df.copy()

    out["revenue_uplift_eur"] = out["revenue_uplift_eur"] * benefit_realization
    out["cost_savings_eur"] = out["cost_savings_eur"] * benefit_realization
    out["implementation_cost_eur"] = out["implementation_cost_eur"] * implementation_cost_multiplier
    out["annual_run_cost_eur"] = out["annual_run_cost_eur"] * run_cost_multiplier

    for col in ["data_readiness", "technology_readiness", "organization_readiness", "skills_readiness"]:
        out[col] = (out[col] + readiness_uplift).clip(0, 100)

    out["autonomy"] = (out["autonomy"] + autonomy_delta).clip(0, 100)
    out["model_uncertainty"] = (out["model_uncertainty"] + uncertainty_delta).clip(0, 100)

    return add_recommendations(add_governance_controls(score_portfolio(out)))


def scenario_delta(baseline: pd.DataFrame, scenario: pd.DataFrame) -> pd.DataFrame:
    cols = ["initiative_id", "initiative_name", "recommendation", "priority_score", "year_1_roi", "risk_score", "readiness_score", "steady_state_net_value_eur"]
    left = baseline[cols].copy().add_suffix("_baseline")
    left = left.rename(columns={"initiative_id_baseline": "initiative_id"})
    right = scenario[cols].copy().add_suffix("_scenario")
    right = right.rename(columns={"initiative_id_scenario": "initiative_id"})
    merged = left.merge(right, on="initiative_id", how="inner")
    merged["priority_delta"] = merged["priority_score_scenario"] - merged["priority_score_baseline"]
    merged["roi_delta"] = merged["year_1_roi_scenario"] - merged["year_1_roi_baseline"]
    merged["decision_changed"] = merged["recommendation_baseline"] != merged["recommendation_scenario"]
    return merged
