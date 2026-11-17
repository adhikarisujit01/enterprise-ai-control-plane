from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


RACI_ROLES = [
    "Executive Sponsor",
    "Business Owner",
    "Technical Owner",
    "AI Governance",
    "Risk / Compliance",
    "Human Reviewer",
]


def _raci_for_row(row: pd.Series) -> dict:
    """Build a deterministic target RACI based on autonomy, governance tier, and risk."""
    tier = int(row["governance_tier"])
    autonomy = float(row["autonomy"])
    risk = float(row["risk_score"])
    ai_type = str(row["ai_type"])

    raci = {
        "Executive Sponsor": "A" if tier >= 3 else "I",
        "Business Owner": "A/R" if tier <= 2 else "R",
        "Technical Owner": "R",
        "AI Governance": "C" if tier <= 2 else "R",
        "Risk / Compliance": "I" if tier == 1 else ("C" if tier == 2 else "R"),
        "Human Reviewer": "I",
    }

    if ai_type == "Agentic AI" or autonomy >= 55:
        raci["Human Reviewer"] = "R" if tier >= 3 else "C"
    if risk >= 75 or tier == 4:
        raci["Executive Sponsor"] = "A"
        raci["AI Governance"] = "R"
        raci["Risk / Compliance"] = "R"
        raci["Human Reviewer"] = "R"
    return raci


def build_raci_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        raci = _raci_for_row(r)
        rows.append({
            "initiative_id": r["initiative_id"],
            "initiative_name": r["initiative_name"],
            "business_function": r["business_function"],
            "governance_tier": int(r["governance_tier"]),
            "recommendation": r["recommendation"],
            "executive_owner": r["executive_owner"],
            "business_owner": r["business_owner"],
            "technical_owner": r["technical_owner"],
            **raci,
        })
    return pd.DataFrame(rows)


def operating_model_summary(df: pd.DataFrame) -> dict:
    return {
        "initiatives": int(len(df)),
        "tier_3_4": int((df["governance_tier"] >= 3).sum()),
        "agentic": int((df["ai_type"] == "Agentic AI").sum()),
        "missing_named_owner": int((~df["has_named_owner"]).sum()),
        "missing_human_override": int(((df["governance_tier"] >= 3) & (~df["has_human_override"])).sum()),
        "missing_audit_logging": int(((df["governance_tier"] >= 2) & (~df["has_audit_logging"])).sum()),
        "missing_kill_switch": int(((df["ai_type"] == "Agentic AI") & (df["governance_tier"] >= 3) & (~df["has_kill_switch"])).sum()),
    }


def target_operating_model_figure() -> go.Figure:
    fig = go.Figure()
    nodes = [
        ("Executive\nSponsor", 0.10, 0.75),
        ("Business\nOwner", 0.30, 0.75),
        ("AI Governance\nForum", 0.50, 0.75),
        ("Risk /\nCompliance", 0.70, 0.75),
        ("Technical\nOwner", 0.90, 0.75),
        ("AI Control Plane", 0.50, 0.42),
        ("Human Reviewer\n/ Exception Team", 0.25, 0.12),
        ("AI Agent /\nCopilot", 0.75, 0.12),
    ]
    edges = [
        (0, 5), (1, 5), (2, 5), (3, 5), (4, 5),
        (5, 6), (5, 7), (6, 7),
    ]
    for a, b in edges:
        x0, y0 = nodes[a][1], nodes[a][2]
        x1, y1 = nodes[b][1], nodes[b][2]
        fig.add_annotation(
            x=x1, y=y1, ax=x0, ay=y0,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.4,
        )
    for label, x, y in nodes:
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers+text", text=[label], textposition="middle center",
            marker=dict(size=78), hoverinfo="skip", showlegend=False,
        ))
    fig.update_xaxes(visible=False, range=[0, 1])
    fig.update_yaxes(visible=False, range=[0, 1])
    fig.update_layout(height=520, margin=dict(l=10, r=10, t=20, b=10))
    return fig


def decision_rights_text(row: pd.Series) -> dict:
    tier = int(row["governance_tier"])
    if tier == 1:
        authority = "Business owner may approve routine use within established policy; periodic review is sufficient."
        escalation = "Escalate material data-quality, customer-impact, or policy exceptions."
    elif tier == 2:
        authority = "Business owner remains accountable; technical owner operates the system with human-on-the-loop monitoring."
        escalation = "Escalate recurring exceptions, sensitive-data issues, or material model drift to AI Governance."
    elif tier == 3:
        authority = "Material decisions require explicit human approval; AI Governance and Risk share control responsibility."
        escalation = "Escalate policy breaches, override failures, or adverse outcomes to the executive sponsor."
    else:
        authority = "No irreversible or high-consequence action may proceed without mandatory human approval and active monitoring."
        escalation = "Immediate executive escalation for control failure, unauthorized action, or inability to rollback."
    return {"decision_authority": authority, "escalation_rule": escalation}
