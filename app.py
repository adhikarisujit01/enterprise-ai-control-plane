from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.scoring import score_portfolio
from src.governance import add_governance_controls
from src.recommendations import add_recommendations
from src.data_generator import write_sample_csv
from src.agent_registry import build_agent_registry, kill_switch_status
from src.control_plane import control_plane_figure, system_flow_figure
from src.scenario import run_portfolio_scenario, scenario_delta
from src.roadmap import build_transformation_roadmap, executive_roadmap_summary
from src.operating_model import build_raci_matrix, operating_model_summary, target_operating_model_figure, decision_rights_text
from src.executive_brief import build_executive_brief

st.set_page_config(page_title="Enterprise AI Control Plane", page_icon="◈", layout="wide", initial_sidebar_state="expanded")

DATA_PATH = Path(__file__).parent / "data" / "ai_portfolio.csv"
if not DATA_PATH.exists():
    write_sample_csv(DATA_PATH)


@st.cache_data
def load_data():
    base = pd.read_csv(DATA_PATH)
    scored = score_portfolio(base)
    governed = add_governance_controls(scored)
    portfolio = add_recommendations(governed)
    registry = build_agent_registry(portfolio)
    return portfolio, registry


def eur(v: float) -> str:
    return f"€{v/1_000_000:.1f}M" if abs(v) >= 1_000_000 else f"€{v/1_000:.0f}K"


df, registry = load_data()

st.markdown("""
<style>
.block-container {padding-top: 1.7rem; padding-bottom: 2.5rem; max-width: 1500px;}
[data-testid="stMetric"] {background: #f7f9fb; border: 1px solid #e5eaf0; padding: 0.85rem; border-radius: 0.65rem;}
div[data-testid="stTabs"] button {font-weight: 600;}
.small-muted {color: #5b6673; font-size: 0.92rem;}
.hero {padding: 0.2rem 0 0.6rem 0;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>Enterprise AI Control Plane</h1></div>', unsafe_allow_html=True)
st.caption("Executive decision support for AI strategy, agentic architecture, governance, permissions, operating model, and value realization.")
st.info("Independent portfolio prototype using synthetic data. The model is transparent and deterministic so assumptions can be challenged in an executive workshop.", icon="ℹ️")

with st.sidebar:
    st.header("Portfolio filters")
    functions = st.multiselect("Business function", sorted(df.business_function.unique()), default=sorted(df.business_function.unique()))
    stages = st.multiselect("Stage", sorted(df.stage.unique()), default=sorted(df.stage.unique()))
    types = st.multiselect("AI type", sorted(df.ai_type.unique()), default=sorted(df.ai_type.unique()))
    st.divider()
    st.markdown("**How to read the prototype**")
    st.caption("1. Portfolio: where to invest")
    st.caption("2. Governance: what must be controlled")
    st.caption("3. Agent Registry: what systems can access")
    st.caption("4. Control Plane: how shared controls fit together")
    st.caption("5. Scenario + Roadmap: what changes and what to do next")
    st.caption("6. Operating Model: who owns the decision")

filtered = df[
    df.business_function.isin(functions)
    & df.stage.isin(stages)
    & df.ai_type.isin(types)
].copy()
filtered_registry = registry[registry.initiative_id.isin(filtered.initiative_id)].copy()

annual_value = filtered.steady_state_net_value_eur.sum()
annual_cost = filtered.annual_run_cost_eur.sum()
accountability = 100 * filtered.has_named_owner.mean() if len(filtered) else 0
coverage = filtered.governance_coverage.mean() if len(filtered) else 0
high_risk = int((filtered.risk_score >= 70).sum())
critical_permission = int((filtered_registry.permission_risk_band == "CRITICAL").sum()) if len(filtered_registry) else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("AI initiatives", len(filtered))
c2.metric("Steady-state net value", eur(annual_value))
c3.metric("Annual run cost", eur(annual_cost))
c4.metric("Governance coverage", f"{coverage:.0f}%")
c5.metric("High-risk systems", high_risk)
c6.metric("Critical permission risk", critical_permission)

portfolio_tab, governance_tab, registry_tab, control_plane_tab, scenario_tab, roadmap_tab, operating_model_tab, brief_tab, detail_tab, method_tab = st.tabs([
    "Portfolio",
    "Governance",
    "Agent Registry",
    "Control Plane",
    "Scenario Simulator",
    "Transformation Roadmap",
    "Operating Model / RACI",
    "Executive Brief",
    "Initiative drill-down",
    "Methodology",
])

with portfolio_tab:
    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Value vs. readiness")
        fig = px.scatter(
            filtered,
            x="readiness_score",
            y="business_value_score",
            size="annual_benefit_eur",
            hover_name="initiative_name",
            hover_data=["recommendation", "risk_score", "year_1_roi"],
            symbol="recommendation",
        )
        fig.update_layout(xaxis_title="Readiness score", yaxis_title="Business value score")
        st.plotly_chart(fig, width="stretch")
    with right:
        st.subheader("Portfolio decisions")
        counts = filtered.recommendation.value_counts().rename_axis("recommendation").reset_index(name="count")
        st.dataframe(counts, hide_index=True, width="stretch")
        st.metric("Named-owner coverage", f"{accountability:.0f}%")

    st.subheader("Executive portfolio view")
    cols = [
        "initiative_name", "business_function", "ai_type", "stage", "business_value_score",
        "readiness_score", "risk_score", "year_1_roi", "priority_score", "governance_tier", "recommendation"
    ]
    view = filtered[cols].sort_values("priority_score", ascending=False).copy()
    view["year_1_roi"] = (view["year_1_roi"] * 100).round(1).astype(str) + "%"
    st.dataframe(view, hide_index=True, width="stretch")

with governance_tab:
    st.subheader("Control gaps")
    gap_df = filtered[filtered.control_gaps != "None"][
        ["initiative_name", "governance_tier", "risk_score", "control_gaps", "oversight_requirement", "executive_owner"]
    ].sort_values(["governance_tier", "risk_score"], ascending=False)
    st.dataframe(gap_df, hide_index=True, width="stretch")

    st.subheader("Agentic systems requiring stronger controls")
    agent_df = filtered[filtered.ai_type == "Agentic AI"][
        ["initiative_name", "autonomy", "risk_score", "governance_tier", "has_human_override", "has_audit_logging", "has_kill_switch", "control_gaps"]
    ].sort_values("risk_score", ascending=False)
    st.dataframe(agent_df, hide_index=True, width="stretch")

with registry_tab:
    st.subheader("Enterprise AI & Agent Registry")
    st.caption("Inventory of systems, models, orchestration, access paths, and permission controls.")

    r1, r2, r3, r4 = st.columns(4)
    agentic_count = int((filtered_registry.ai_type == "Agentic AI").sum())
    broad_identity = int((filtered_registry.identity_mode == "Shared / broad identity").sum())
    excessive = int((filtered_registry.least_privilege == False).sum())
    missing_kill = int(((filtered_registry.ai_type == "Agentic AI") & (filtered_registry.governance_tier >= 3) & (~filtered_registry.kill_switch)).sum())
    r1.metric("Agentic systems", agentic_count)
    r2.metric("Broad/shared identities", broad_identity)
    r3.metric("Least-privilege violations", excessive)
    r4.metric("Required kill switches missing", missing_kill)

    show = filtered_registry[[
        "system_name", "ai_type", "stage", "provider", "model", "orchestrator", "data_domains", "tools",
        "identity_mode", "least_privilege", "production_access", "secrets_access", "external_action_authority",
        "permission_risk_score", "permission_risk_band", "permission_control_gaps"
    ]].sort_values("permission_risk_score", ascending=False)
    st.dataframe(show, hide_index=True, width="stretch")

    st.subheader("Permission-risk distribution")
    risk_counts = filtered_registry.permission_risk_band.value_counts().reindex(["LOW", "MODERATE", "HIGH", "CRITICAL"], fill_value=0).rename_axis("risk_band").reset_index(name="systems")
    st.bar_chart(risk_counts.set_index("risk_band"))

with control_plane_tab:
    st.subheader("Enterprise AI Control Plane")
    st.caption("A shared control path for identity, policy, orchestration, model access, tools, data, and observability.")
    st.plotly_chart(control_plane_figure(), width="stretch")

    if len(filtered_registry):
        selected_system = st.selectbox("Inspect a system control path", filtered_registry.system_name.tolist(), key="control_plane_system")
        agent = filtered_registry[filtered_registry.system_name == selected_system].iloc[0]
        st.plotly_chart(system_flow_figure(agent), width="stretch")

        a, b, c, d = st.columns(4)
        a.metric("Permission risk", f"{agent.permission_risk_score:.0f}/100")
        b.metric("Risk band", agent.permission_risk_band)
        c.metric("Governance tier", int(agent.governance_tier))
        d.metric("Kill-switch status", kill_switch_status(agent))

        st.markdown("#### Access profile")
        st.write({
            "Provider / model": f"{agent.provider} / {agent.model}",
            "Orchestrator": agent.orchestrator,
            "Identity": agent.identity_mode,
            "Data domains": agent.data_domains,
            "Tools": agent.tools,
            "Production access": bool(agent.production_access),
            "Secrets access": bool(agent.secrets_access),
            "Network access": bool(agent.network_access),
            "External action authority": bool(agent.external_action_authority),
            "Persistent memory": bool(agent.persistent_memory),
            "Control gaps": agent.permission_control_gaps,
        })

        if agent.ai_type == "Agentic AI":
            st.markdown("#### Kill-switch simulation")
            reason = st.selectbox(
                "Trigger condition",
                ["Unauthorized action attempt", "Cost anomaly", "Policy violation", "Unexpected tool behavior", "Manual executive intervention"],
            )
            if st.button("Simulate emergency stop", type="primary"):
                if bool(agent.kill_switch):
                    st.success(f"{selected_system} isolated. Tool access revoked, new actions blocked, and incident logged. Trigger: {reason}.")
                else:
                    st.error(f"Emergency stop failed: {selected_system} has no registered kill switch. Escalate immediately to {agent.technical_owner} and {agent.executive_owner}.")


with scenario_tab:
    st.subheader("Executive Scenario Simulator")
    st.caption("Stress-test the AI portfolio before committing capital. All assumptions are explicit and the decision engine is re-run deterministically.")

    s1, s2, s3 = st.columns(3)
    benefit_pct = s1.slider("Benefit realization", 30, 130, 100, 5, help="Percent of forecast revenue uplift and cost savings actually realized.")
    impl_pct = s2.slider("Implementation cost", 70, 180, 100, 5, help="Scenario multiplier on implementation cost.")
    run_pct = s3.slider("Annual run cost", 70, 180, 100, 5, help="Scenario multiplier on recurring AI run cost.")

    s4, s5, s6 = st.columns(3)
    readiness_uplift = s4.slider("Readiness uplift (points)", -20, 25, 0, 5)
    autonomy_delta = s5.slider("Autonomy change (points)", -20, 25, 0, 5)
    uncertainty_delta = s6.slider("Model uncertainty change (points)", -20, 25, 0, 5)

    raw_base = pd.read_csv(DATA_PATH)
    scenario_df = run_portfolio_scenario(
        raw_base,
        benefit_realization=benefit_pct / 100,
        implementation_cost_multiplier=impl_pct / 100,
        run_cost_multiplier=run_pct / 100,
        readiness_uplift=readiness_uplift,
        autonomy_delta=autonomy_delta,
        uncertainty_delta=uncertainty_delta,
    )
    delta = scenario_delta(df, scenario_df)

    baseline_value = df.steady_state_net_value_eur.sum()
    scenario_value = scenario_df.steady_state_net_value_eur.sum()
    changed = int(delta.decision_changed.sum())
    high_risk_scenario = int((scenario_df.risk_score >= 70).sum())

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Scenario net value", eur(scenario_value), delta=eur(scenario_value - baseline_value))
    q2.metric("Decisions changed", changed)
    q3.metric("Scale now", int((scenario_df.recommendation == "SCALE NOW").sum()))
    q4.metric("High-risk systems", high_risk_scenario)

    st.markdown("#### Decision movement")
    movement = delta[[
        "initiative_name_baseline", "recommendation_baseline", "recommendation_scenario",
        "priority_score_baseline", "priority_score_scenario", "priority_delta", "decision_changed"
    ]].rename(columns={"initiative_name_baseline": "initiative_name"})
    movement = movement.sort_values(["decision_changed", "priority_delta"], ascending=[False, True])
    st.dataframe(movement, hide_index=True, width="stretch")

    st.markdown("#### Scenario portfolio")
    scenario_view = scenario_df[[
        "initiative_name", "business_function", "recommendation", "priority_score",
        "business_value_score", "readiness_score", "risk_score", "year_1_roi", "governance_tier"
    ]].sort_values("priority_score", ascending=False).copy()
    scenario_view["year_1_roi"] = (scenario_view["year_1_roi"] * 100).round(1).astype(str) + "%"
    st.dataframe(scenario_view, hide_index=True, width="stretch")

with roadmap_tab:
    st.subheader("AI Transformation Roadmap")
    st.caption("Translate portfolio choices into an executive sequence of scale, pilot, redesign, hold, and stop actions.")
    roadmap = build_transformation_roadmap(filtered)
    summary = executive_roadmap_summary(filtered)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Scale", summary["scale"])
    m2.metric("Pilot", summary["pilot"])
    m3.metric("Redesign", summary["redesign"])
    m4.metric("Hold", summary["hold"])
    m5.metric("Stop", summary["stop"])
    m6.metric("Urgent governance", summary["immediate_governance"])

    horizon_order = ["Immediate", "0-60 days", "0-90 days", "3-6 months"]
    for horizon in horizon_order:
        slice_df = roadmap[roadmap.horizon == horizon]
        if len(slice_df):
            st.markdown(f"#### {horizon}")
            st.dataframe(
                slice_df[["initiative_name", "business_function", "decision", "action", "executive_owner", "governance_tier", "next_step"]],
                hide_index=True,
                width="stretch",
            )

    st.markdown("#### Executive sequence")
    st.markdown(
        "1. **Stop leakage first:** close tier-3/4 governance gaps and stop low-value initiatives.  "
        "\n2. **Prove value next:** run bounded pilots with explicit scale/stop gates.  "
        "\n3. **Scale the winners:** expand high-value, high-readiness initiatives behind shared control-plane standards.  "
        "\n4. **Revisit the portfolio quarterly:** re-score economics, readiness, autonomy, permissions, and accountability."
    )


with operating_model_tab:
    st.subheader("Target AI Operating Model & Decision Rights")
    st.caption("Translate AI governance into explicit accountability, decision authority, escalation paths, and human oversight.")

    osum = operating_model_summary(filtered)
    o1, o2, o3, o4, o5 = st.columns(5)
    o1.metric("Tier 3/4 systems", osum["tier_3_4"])
    o2.metric("Missing named owner", osum["missing_named_owner"])
    o3.metric("Missing human override", osum["missing_human_override"])
    o4.metric("Missing audit logging", osum["missing_audit_logging"])
    o5.metric("Missing kill switch", osum["missing_kill_switch"])

    st.plotly_chart(target_operating_model_figure(), width="stretch")

    st.markdown("#### Portfolio RACI")
    raci = build_raci_matrix(filtered)
    raci_view = raci[[
        "initiative_name", "business_function", "governance_tier", "recommendation",
        "Executive Sponsor", "Business Owner", "Technical Owner", "AI Governance",
        "Risk / Compliance", "Human Reviewer"
    ]].sort_values(["governance_tier", "initiative_name"], ascending=[False, True])
    st.dataframe(raci_view, hide_index=True, width="stretch")
    st.caption("R = Responsible · A = Accountable · C = Consulted · I = Informed. A/R indicates combined accountability and execution ownership for lower-risk systems.")

    if len(filtered):
        st.markdown("#### Initiative decision rights")
        om_name = st.selectbox("Inspect operating model", filtered.initiative_name.tolist(), key="operating_model_system")
        om_row = filtered[filtered.initiative_name == om_name].iloc[0]
        om_raci = raci[raci.initiative_name == om_name].iloc[0]
        rights = decision_rights_text(om_row)
        left, right = st.columns([1, 1.2])
        with left:
            st.write({
                "Executive owner": om_row.executive_owner,
                "Business owner": om_row.business_owner,
                "Technical owner": om_row.technical_owner,
                "Governance tier": int(om_row.governance_tier),
                "Oversight": om_row.oversight_requirement,
                "Control gaps": om_row.control_gaps,
            })
        with right:
            st.markdown(f"**Decision authority:** {rights['decision_authority']}")
            st.markdown(f"**Escalation rule:** {rights['escalation_rule']}")
            st.markdown(
                f"**Target RACI:** Executive Sponsor `{om_raci['Executive Sponsor']}` · "
                f"Business Owner `{om_raci['Business Owner']}` · Technical Owner `{om_raci['Technical Owner']}` · "
                f"AI Governance `{om_raci['AI Governance']}` · Risk/Compliance `{om_raci['Risk / Compliance']}` · "
                f"Human Reviewer `{om_raci['Human Reviewer']}`"
            )

with brief_tab:
    st.subheader("Executive AI Transformation Brief")
    st.caption("Generate a management-ready summary from the same deterministic portfolio, governance, and operating-model logic.")
    brief = build_executive_brief(filtered)
    b1, b2, b3 = st.columns(3)
    b1.metric("Initiatives covered", len(filtered))
    b2.metric("High-risk systems", int((filtered.risk_score >= 70).sum()))
    b3.metric("Governance gaps", int((filtered.control_gaps != "None").sum()))

    st.download_button(
        "Download executive brief (.md)",
        data=brief,
        file_name="enterprise_ai_transformation_executive_brief.md",
        mime="text/markdown",
        type="primary",
    )
    st.markdown(brief)

with detail_tab:
    selected_name = st.selectbox("Select initiative", filtered.initiative_name.tolist() if len(filtered) else df.initiative_name.tolist())
    row = df[df.initiative_name == selected_name].iloc[0]
    agent = registry[registry.initiative_id == row.initiative_id].iloc[0]

    a, b, c, d, e = st.columns(5)
    a.metric("Recommendation", row.recommendation)
    b.metric("Priority", f"{row.priority_score:.0f}/100")
    c.metric("Business risk", f"{row.risk_score:.0f}/100")
    d.metric("Permission risk", f"{agent.permission_risk_score:.0f}/100")
    e.metric("Governance tier", int(row.governance_tier))

    st.markdown(f"**Rationale:** {row.rationale}")
    st.markdown(f"**Oversight:** {row.oversight_requirement}")
    st.markdown(f"**Governance gaps:** {row.control_gaps}")
    st.markdown(f"**Permission gaps:** {agent.permission_control_gaps}")

    st.subheader("Economics")
    econ = pd.DataFrame({
        "Metric": ["Annual benefit", "Implementation cost", "Annual run cost", "Steady-state net value", "Year-1 ROI", "Payback years"],
        "Value": [
            eur(row.annual_benefit_eur), eur(row.implementation_cost_eur), eur(row.annual_run_cost_eur),
            eur(row.steady_state_net_value_eur), f"{row.year_1_roi*100:.1f}%",
            "N/A" if pd.isna(row.payback_years) or row.payback_years < 0 else f"{row.payback_years:.2f}",
        ],
    })
    st.dataframe(econ, hide_index=True, width="stretch")

    st.subheader("Ownership & decision authority")
    st.write({
        "Executive owner": row.executive_owner,
        "Business owner": row.business_owner,
        "Technical owner": row.technical_owner,
        "Human override": bool(row.has_human_override),
        "Audit logging": bool(row.has_audit_logging),
        "Kill switch": bool(row.has_kill_switch),
    })

with method_tab:
    st.markdown("""
### Decision model
The prototype scores each AI initiative across four dimensions:

1. **Business value** — direct economics, customer impact, and strategic alignment.
2. **Readiness** — data, technology, organization, and skills readiness.
3. **Risk** — autonomy, consequence severity, data sensitivity, regulatory exposure, and model uncertainty.
4. **Economics** — year-one ROI, steady-state net value, and payback.

The decision engine converts those signals into one of five actions: **Scale Now, Controlled Pilot, Redesign, Hold, or Stop**.

### Governance model
Governance tiers rise with autonomy, consequence severity, regulatory exposure, and overall risk. Higher tiers require progressively stronger human oversight, logging, ownership, and—where applicable—agent kill switches.

### Permission model
The Agent Registry adds a second control lens: **what the AI system can actually reach and do**. Permission risk rises with production access, secrets access, network connectivity, persistent memory, external action authority, broad identities, lack of least privilege, and missing operational controls.

### Control-plane concept
The architecture separates business workflows from shared controls for identity, policy enforcement, orchestration, model routing, tools/data access, and observability. The goal is to make heterogeneous AI systems governable as shared enterprise infrastructure rather than isolated experiments.

### Scenario and roadmap model
The Scenario Simulator changes explicit value, cost, readiness, autonomy, and uncertainty assumptions and then re-runs the same scoring, governance, and recommendation logic. The Transformation Roadmap converts decisions into deterministic action horizons and ownership-oriented next steps.

### Public research basis
The problem framing is informed by recent public BCG research on enterprise AI transformation and agent governance:

- **Client Zero: Inside BCG's AI Transformation (Nov. 11, 2026):** common architecture, workflow redesign, reusable AI capabilities, and explicit human accountability.
- **Enterprise AI Control Plane (Aug. 14, 2026):** centralized identity, policy enforcement, visibility, and governance across heterogeneous agents.
- **Operationalizing AI Governance (Nov. 13, 2026):** a practical gap can exist between governance foundations and day-to-day operational controls.

The public research motivates the problem statement only. The synthetic data, score weights, thresholds, governance tiers, and recommendation logic are original prototype choices. Full links are documented in `docs/research_basis.md`.

### Important
This is an independent portfolio project using synthetic data. It is not affiliated with BCG, BCG Platinion, Deloitte, or any client organization. The scoring model is intentionally transparent and should be treated as a decision-support framework, not a production policy engine.
""")
