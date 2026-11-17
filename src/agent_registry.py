from __future__ import annotations

import hashlib
import random
from typing import Iterable

import pandas as pd

PROVIDERS = ["Azure OpenAI", "OpenAI", "Anthropic", "AWS Bedrock", "Internal ML Platform"]
MODELS = {
    "Azure OpenAI": ["GPT-5-class", "GPT-4.1-class"],
    "OpenAI": ["GPT-5-class", "o-series reasoning"],
    "Anthropic": ["Claude-class"],
    "AWS Bedrock": ["Claude-class", "Llama-class"],
    "Internal ML Platform": ["Gradient-boosted model", "Fine-tuned encoder", "Forecasting ensemble"],
}
ORCHESTRATORS = ["Semantic Kernel", "LangGraph", "Bedrock Agents", "Internal Orchestrator", "N/A"]
DATA_DOMAINS = ["CRM", "ERP", "Finance", "HRIS", "Data Lake", "Contracts", "Product Analytics", "Customer Support"]
TOOLS = ["CRM write", "ERP read", "Payments API", "Email", "Web search", "SQL warehouse", "Ticketing", "Pricing API", "Contract store"]


def _rng_for(value: str) -> random.Random:
    seed = int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)
    return random.Random(seed)


def _pick_many(rng: random.Random, values: Iterable[str], k_low: int, k_high: int) -> list[str]:
    values = list(values)
    k = min(len(values), rng.randint(k_low, k_high))
    return sorted(rng.sample(values, k=k))


def build_agent_registry(portfolio: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in portfolio.iterrows():
        rng = _rng_for(str(row["initiative_id"]))
        is_predictive = row["ai_type"] == "Predictive ML"
        is_agentic = row["ai_type"] == "Agentic AI"

        provider = "Internal ML Platform" if is_predictive and rng.random() < 0.72 else rng.choice(PROVIDERS[:-1])
        model = rng.choice(MODELS[provider])
        orchestrator = "N/A" if is_predictive else rng.choice(ORCHESTRATORS[:-1])

        data_domains = _pick_many(rng, DATA_DOMAINS, 1, 3)
        tools = _pick_many(rng, TOOLS, 1 if is_agentic else 0, 4 if is_agentic else 2)
        if not is_agentic and rng.random() < 0.55:
            tools = []

        can_write = is_agentic and any("write" in tool.lower() or "api" in tool.lower() or tool == "Email" for tool in tools)
        external_actions = is_agentic and (can_write or rng.random() < 0.45)
        prod_access = row["stage"] == "Production" or (row["stage"] == "Pilot" and rng.random() < 0.55)
        secrets_access = is_agentic and rng.random() < 0.28
        network_access = (not is_predictive) and rng.random() < 0.62
        scoped_identity = rng.random() < (0.82 if row["governance_tier"] <= 2 else 0.64)
        least_privilege = rng.random() < (0.78 if row["governance_tier"] <= 2 else 0.58)
        memory_enabled = (not is_predictive) and rng.random() < 0.48

        rows.append({
            "initiative_id": row["initiative_id"],
            "system_name": row["initiative_name"],
            "ai_type": row["ai_type"],
            "stage": row["stage"],
            "provider": provider,
            "model": model,
            "orchestrator": orchestrator,
            "data_domains": ", ".join(data_domains),
            "tools": ", ".join(tools) if tools else "None",
            "identity_mode": "Scoped service identity" if scoped_identity else "Shared / broad identity",
            "least_privilege": least_privilege,
            "production_access": prod_access,
            "secrets_access": secrets_access,
            "network_access": network_access,
            "external_action_authority": external_actions,
            "persistent_memory": memory_enabled,
            "human_override": bool(row["has_human_override"]),
            "audit_logging": bool(row["has_audit_logging"]),
            "kill_switch": bool(row["has_kill_switch"]),
            "governance_tier": int(row["governance_tier"]),
            "risk_score": float(row["risk_score"]),
            "executive_owner": row["executive_owner"],
            "technical_owner": row["technical_owner"],
        })

    registry = pd.DataFrame(rows)
    return add_permission_risk(registry)


def add_permission_risk(registry: pd.DataFrame) -> pd.DataFrame:
    out = registry.copy()

    def risk(row: pd.Series) -> tuple[float, str]:
        score = 0.0
        gaps: list[str] = []
        if row["external_action_authority"]:
            score += 24
        if row["production_access"]:
            score += 16
        if row["secrets_access"]:
            score += 18
            gaps.append("Secrets access")
        if row["network_access"]:
            score += 10
        if row["persistent_memory"]:
            score += 8
        if not row["least_privilege"]:
            score += 18
            gaps.append("Least-privilege violation")
        if row["identity_mode"] != "Scoped service identity":
            score += 16
            gaps.append("Broad/shared identity")
        if row["governance_tier"] >= 3 and not row["human_override"]:
            score += 18
            gaps.append("No human override")
        if row["governance_tier"] >= 2 and not row["audit_logging"]:
            score += 14
            gaps.append("No audit logging")
        if row["ai_type"] == "Agentic AI" and row["governance_tier"] >= 3 and not row["kill_switch"]:
            score += 20
            gaps.append("No kill switch")

        score = min(100.0, score)
        return round(score, 1), ", ".join(gaps) if gaps else "None"

    pairs = out.apply(risk, axis=1)
    out["permission_risk_score"] = [p[0] for p in pairs]
    out["permission_control_gaps"] = [p[1] for p in pairs]
    out["permission_risk_band"] = pd.cut(
        out["permission_risk_score"],
        bins=[-0.1, 29.9, 59.9, 79.9, 100.0],
        labels=["LOW", "MODERATE", "HIGH", "CRITICAL"],
    ).astype(str)
    return out


def kill_switch_status(row: pd.Series) -> str:
    if row["ai_type"] != "Agentic AI":
        return "Not required for non-agentic system"
    if row["governance_tier"] < 3:
        return "Recommended"
    return "READY" if bool(row["kill_switch"]) else "MISSING — blocking control"
