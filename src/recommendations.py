from __future__ import annotations

import pandas as pd


def _decision(row: pd.Series) -> str:
    if row["business_value_score"] < 38 or row["year_1_roi"] < -0.35:
        return "STOP"
    if row["business_value_score"] >= 68 and (row["readiness_score"] < 45 or row["risk_score"] > 76):
        return "REDESIGN"
    if row["priority_score"] >= 70 and row["readiness_score"] >= 60 and row["risk_score"] <= 68 and row["year_1_roi"] > 0:
        return "SCALE NOW"
    if row["priority_score"] >= 52 and row["business_value_score"] >= 50:
        return "CONTROLLED PILOT"
    return "HOLD"


def _rationale(row: pd.Series) -> str:
    decision = row["recommendation"]
    if decision == "SCALE NOW":
        return "High value and readiness with acceptable risk; move toward scaled adoption with tier-appropriate controls."
    if decision == "CONTROLLED PILOT":
        return "Promising value case, but evidence or readiness is not yet sufficient for full-scale deployment."
    if decision == "REDESIGN":
        return "Strategically valuable, but current risk/readiness profile requires workflow, ownership, or architecture redesign."
    if decision == "STOP":
        return "Weak economics or strategic value relative to cost and risk; capital is better allocated elsewhere."
    return "Maintain optionality while resolving economics, readiness, or ownership questions."


def add_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["recommendation"] = out.apply(_decision, axis=1)
    out["rationale"] = out.apply(_rationale, axis=1)
    return out
