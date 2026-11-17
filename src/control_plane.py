from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def control_plane_figure() -> go.Figure:
    labels = [
        "Business Process",
        "AI Agent / Copilot",
        "Identity & Access",
        "Policy Engine",
        "Agent Orchestrator",
        "Model Gateway",
        "Tools & APIs",
        "Enterprise Data",
        "Observability & Audit",
    ]
    idx = {name: i for i, name in enumerate(labels)}
    edges = [
        ("Business Process", "AI Agent / Copilot", 10),
        ("AI Agent / Copilot", "Identity & Access", 10),
        ("Identity & Access", "Policy Engine", 10),
        ("Policy Engine", "Agent Orchestrator", 10),
        ("Agent Orchestrator", "Model Gateway", 6),
        ("Agent Orchestrator", "Tools & APIs", 4),
        ("Tools & APIs", "Enterprise Data", 4),
        ("Model Gateway", "Observability & Audit", 6),
        ("Tools & APIs", "Observability & Audit", 4),
    ]
    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(label=labels, pad=18, thickness=20),
                link=dict(
                    source=[idx[a] for a, _, _ in edges],
                    target=[idx[b] for _, b, _ in edges],
                    value=[v for _, _, v in edges],
                ),
            )
        ]
    )
    fig.update_layout(title_text="Enterprise AI control-plane flow", font_size=12, height=480)
    return fig


def system_flow_figure(agent: pd.Series) -> go.Figure:
    labels = [
        "User / Workflow",
        agent["system_name"],
        "Scoped Identity" if agent["identity_mode"] == "Scoped service identity" else "Broad Identity",
        "Policy Engine",
        agent["orchestrator"],
        agent["model"],
        "Enterprise Tools",
        "Enterprise Data",
        "Observability",
    ]
    edges = [(0,1,10),(1,2,10),(2,3,10),(3,4,10),(4,5,6),(4,6,4),(6,7,4),(5,8,6),(6,8,4)]
    fig = go.Figure(
        data=[go.Sankey(
            node=dict(label=labels, pad=16, thickness=18),
            link=dict(source=[a for a,_,_ in edges], target=[b for _,b,_ in edges], value=[v for _,_,v in edges]),
        )]
    )
    fig.update_layout(title_text=f"Control path — {agent['system_name']}", font_size=11, height=430)
    return fig
