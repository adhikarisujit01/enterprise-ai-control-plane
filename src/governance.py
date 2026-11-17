from __future__ import annotations

import pandas as pd


def governance_tier(row: pd.Series) -> int:
    if row["autonomy"] >= 75 and (row["consequence_severity"] >= 70 or row["regulatory_exposure"] >= 70):
        return 4
    if row["autonomy"] >= 55 or row["risk_score"] >= 65:
        return 3
    if row["risk_score"] >= 40 or row["data_sensitivity"] >= 55:
        return 2
    return 1


def human_oversight_requirement(tier: int) -> str:
    return {
        1: "Periodic human review",
        2: "Human-on-the-loop monitoring",
        3: "Human approval for material decisions",
        4: "Mandatory approval + continuous monitoring + rollback",
    }[tier]


def add_governance_controls(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["governance_tier"] = out.apply(governance_tier, axis=1)
    out["oversight_requirement"] = out["governance_tier"].map(human_oversight_requirement)

    def control_gap(row):
        gaps = []
        if not row["has_named_owner"]:
            gaps.append("Named owner")
        if row["governance_tier"] >= 3 and not row["has_human_override"]:
            gaps.append("Human override")
        if row["governance_tier"] >= 2 and not row["has_audit_logging"]:
            gaps.append("Audit logging")
        if row["ai_type"] == "Agentic AI" and row["governance_tier"] >= 3 and not row["has_kill_switch"]:
            gaps.append("Kill switch")
        return ", ".join(gaps) if gaps else "None"

    out["control_gaps"] = out.apply(control_gap, axis=1)
    out["governance_coverage"] = out.apply(
        lambda r: round(100 * (4 - (0 if r["control_gaps"] == "None" else len(r["control_gaps"].split(", ")))) / 4, 1),
        axis=1,
    )
    return out
