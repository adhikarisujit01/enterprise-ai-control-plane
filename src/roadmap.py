from __future__ import annotations

import pandas as pd


def build_transformation_roadmap(df: pd.DataFrame) -> pd.DataFrame:
    """Translate portfolio decisions into a deterministic executive transformation roadmap."""
    rows = []
    for _, r in df.sort_values("priority_score", ascending=False).iterrows():
        gaps = r.get("control_gaps", "None")
        decision = r["recommendation"]

        if decision == "SCALE NOW":
            horizon = "0-90 days"
            action = "Scale with guardrails"
            next_step = "Confirm KPI baseline, production controls, accountable owner, and capacity plan; then expand adoption."
        elif decision == "CONTROLLED PILOT":
            horizon = "0-90 days"
            action = "Run evidence-building pilot"
            next_step = "Define success metrics, bounded users/workflows, human oversight, and an explicit scale/stop gate."
        elif decision == "REDESIGN":
            horizon = "0-60 days"
            action = "Redesign before further deployment"
            next_step = "Resolve architecture, workflow, ownership, permission, or risk gaps before committing more capital."
        elif decision == "HOLD":
            horizon = "3-6 months"
            action = "Hold and close readiness gaps"
            next_step = "Improve data/technology/organizational readiness and revalidate the value case at the next portfolio review."
        else:
            horizon = "Immediate"
            action = "Stop / reallocate"
            next_step = "Stop additional investment, capture lessons learned, and redirect budget toward higher-value initiatives."

        if gaps != "None":
            next_step += f" Governance gaps to close: {gaps}."

        rows.append({
            "initiative_id": r["initiative_id"],
            "initiative_name": r["initiative_name"],
            "business_function": r["business_function"],
            "decision": decision,
            "horizon": horizon,
            "action": action,
            "priority_score": r["priority_score"],
            "governance_tier": int(r["governance_tier"]),
            "executive_owner": r["executive_owner"],
            "next_step": next_step,
        })

    return pd.DataFrame(rows)


def executive_roadmap_summary(df: pd.DataFrame) -> dict:
    roadmap = build_transformation_roadmap(df)
    return {
        "scale": int((roadmap.decision == "SCALE NOW").sum()),
        "pilot": int((roadmap.decision == "CONTROLLED PILOT").sum()),
        "redesign": int((roadmap.decision == "REDESIGN").sum()),
        "hold": int((roadmap.decision == "HOLD").sum()),
        "stop": int((roadmap.decision == "STOP").sum()),
        "immediate_governance": int(((df.governance_tier >= 3) & (df.control_gaps != "None")).sum()),
    }
