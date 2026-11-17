from __future__ import annotations

from datetime import date
import pandas as pd

from src.roadmap import build_transformation_roadmap, executive_roadmap_summary
from src.operating_model import operating_model_summary


def _eur(v: float) -> str:
    return f"€{v/1_000_000:.1f}M" if abs(v) >= 1_000_000 else f"€{v/1_000:.0f}K"


def build_executive_brief(df: pd.DataFrame, title: str = "Enterprise AI Transformation Executive Brief") -> str:
    roadmap = build_transformation_roadmap(df)
    rsum = executive_roadmap_summary(df)
    osum = operating_model_summary(df)

    total_benefit = float(df["annual_benefit_eur"].sum())
    total_run_cost = float(df["annual_run_cost_eur"].sum())
    steady_value = float(df["steady_state_net_value_eur"].sum())
    governance = float(df["governance_coverage"].mean()) if len(df) else 0.0
    portfolio_roi = (total_benefit - total_run_cost) / total_run_cost if total_run_cost else 0.0

    top_scale = df[df["recommendation"] == "SCALE NOW"].sort_values("priority_score", ascending=False).head(5)
    top_risk = df.sort_values(["risk_score", "governance_tier"], ascending=False).head(5)
    redesign = roadmap[roadmap["decision"] == "REDESIGN"].head(5)

    lines = [
        f"# {title}",
        "",
        f"**Generated:** {date.today().isoformat()}",
        "",
        "> Independent portfolio prototype using synthetic enterprise data. It is designed to support an executive workshop, not to replace management judgment or production governance policy.",
        "",
        "## Executive summary",
        "",
        f"The portfolio contains **{len(df)} AI initiatives** with **{_eur(total_benefit)} forecast annual benefit** and **{_eur(total_run_cost)} recurring annual run cost**. The modeled steady-state net value is **{_eur(steady_value)}**, equivalent to a simplified run-rate value/cost ratio of **{portfolio_roi:.1f}x**. The immediate management priority is to scale proven initiatives only where accountability and operational controls are complete, while redesigning high-value systems whose autonomy or control posture is ahead of organizational readiness.",
        "",
        "## Portfolio snapshot",
        "",
        f"- **Scale now:** {rsum['scale']}",
        f"- **Controlled pilot:** {rsum['pilot']}",
        f"- **Redesign:** {rsum['redesign']}",
        f"- **Hold:** {rsum['hold']}",
        f"- **Stop / reallocate:** {rsum['stop']}",
        f"- **Average governance coverage:** {governance:.0f}%",
        f"- **Tier 3/4 systems:** {osum['tier_3_4']}",
        f"- **Agentic systems:** {osum['agentic']}",
        "",
        "## Questions for the executive team",
        "",
        "1. Which workflows create enough differentiated value to justify redesign rather than simple task automation?",
        "2. Where should human judgment remain decisive even if technical autonomy is possible?",
        "3. Which controls should be standardized centrally through the AI platform, and which should remain domain-specific?",
        "4. Which initiatives have attractive economics but insufficient organizational or technical readiness?",
        "5. What evidence must each pilot produce before capital and autonomy increase?",
        "",
        "## Operating-model and control gaps",
        "",
        f"- Missing named owner: **{osum['missing_named_owner']}**",
        f"- Tier 3/4 systems missing human override: **{osum['missing_human_override']}**",
        f"- Tier 2+ systems missing audit logging: **{osum['missing_audit_logging']}**",
        f"- Agentic Tier 3/4 systems missing kill switch: **{osum['missing_kill_switch']}**",
        "",
        "## Highest-priority scale candidates",
        "",
    ]

    if len(top_scale):
        for _, r in top_scale.iterrows():
            lines.append(
                f"- **{r['initiative_name']}** — priority {r['priority_score']:.0f}/100; "
                f"year-one ROI {r['year_1_roi']*100:.1f}%; governance tier {int(r['governance_tier'])}."
            )
    else:
        lines.append("- No initiatives currently meet the Scale Now threshold.")

    lines += ["", "## Highest-risk initiatives", ""]
    for _, r in top_risk.iterrows():
        lines.append(
            f"- **{r['initiative_name']}** — risk {r['risk_score']:.0f}/100; tier {int(r['governance_tier'])}; "
            f"control gaps: {r['control_gaps']}."
        )

    lines += ["", "## Redesign queue", ""]
    if len(redesign):
        for _, r in redesign.iterrows():
            lines.append(f"- **{r['initiative_name']}** — {r['next_step']}")
    else:
        lines.append("- No initiatives currently sit in the Redesign category.")

    lines += [
        "",
        "## Recommended 90-day sequence",
        "",
        "**0–30 days — establish control and accountability.** Resolve Tier 3/4 ownership, human-override, logging, permission, and kill-switch gaps. Freeze additional autonomy for systems without complete controls.",
        "",
        "**30–60 days — prove value in bounded workflows.** Run controlled pilots with explicit KPIs, limited users/actions, named owners, and pre-agreed scale/stop gates.",
        "",
        "**60–90 days — scale through shared architecture.** Expand the strongest initiatives behind standardized identity, policy, orchestration, observability, audit, and incident controls. Stop or reallocate capital from persistently weak value cases.",
        "",
        "## Design principle",
        "",
        "The prototype treats AI transformation as a combined **strategy + technology + operating-model** problem. A strong model is not sufficient: value depends on workflow redesign, clear decision rights, technical controls, and the ability to change course as economics and technology evolve.",
        "",
        "## Methodology note",
        "",
        "The recommendation engine combines business value, readiness, risk, economics, governance tier, and operational controls. The model is deterministic and transparent by design. Its purpose is to make assumptions visible and challengeable rather than present a black-box score as objective truth.",
    ]
    return "\n".join(lines)
