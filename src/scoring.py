from __future__ import annotations

import numpy as np
import pandas as pd


def _clip(x):
    return np.clip(x, 0, 100)


def score_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Value combines direct economics with customer and strategic impact.
    max_benefit = (out["revenue_uplift_eur"] + out["cost_savings_eur"]).max()
    econ_value = ((out["revenue_uplift_eur"] + out["cost_savings_eur"]) / max_benefit * 100).fillna(0)
    out["business_value_score"] = _clip(
        0.45 * econ_value
        + 0.25 * out["customer_impact"]
        + 0.30 * out["strategic_alignment"]
    ).round(1)

    out["readiness_score"] = _clip(
        0.30 * out["data_readiness"]
        + 0.25 * out["technology_readiness"]
        + 0.25 * out["organization_readiness"]
        + 0.20 * out["skills_readiness"]
    ).round(1)

    out["risk_score"] = _clip(
        0.30 * out["autonomy"]
        + 0.25 * out["consequence_severity"]
        + 0.20 * out["data_sensitivity"]
        + 0.15 * out["regulatory_exposure"]
        + 0.10 * out["model_uncertainty"]
    ).round(1)

    out["annual_benefit_eur"] = out["revenue_uplift_eur"] + out["cost_savings_eur"]
    out["year_1_cost_eur"] = out["implementation_cost_eur"] + out["annual_run_cost_eur"]
    out["steady_state_net_value_eur"] = out["annual_benefit_eur"] - out["annual_run_cost_eur"]
    out["year_1_roi"] = ((out["annual_benefit_eur"] - out["year_1_cost_eur"]) / out["year_1_cost_eur"]).round(3)
    out["payback_years"] = (out["implementation_cost_eur"] / out["steady_state_net_value_eur"].replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).round(2)

    roi_score = _clip(50 + 40 * out["year_1_roi"])  # 0% ROI=50; 125% ROI~=100
    out["priority_score"] = _clip(
        0.38 * out["business_value_score"]
        + 0.27 * out["readiness_score"]
        + 0.20 * roi_score
        + 0.15 * (100 - out["risk_score"])
    ).round(1)

    return out
