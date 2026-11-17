from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42

USE_CASES = [
    ("Customer Service Agent", "Customer Service", "Agentic AI"),
    ("Pricing Optimization Agent", "Commercial", "Agentic AI"),
    ("Finance Close Copilot", "Finance", "GenAI Copilot"),
    ("Sales Proposal Copilot", "Sales", "GenAI Copilot"),
    ("Procurement Negotiation Agent", "Procurement", "Agentic AI"),
    ("HR Policy Assistant", "HR", "RAG Assistant"),
    ("Legal Contract Reviewer", "Legal", "RAG Assistant"),
    ("Demand Forecasting Model", "Supply Chain", "Predictive ML"),
    ("Fraud Detection Model", "Risk", "Predictive ML"),
    ("Marketing Content Copilot", "Marketing", "GenAI Copilot"),
    ("Executive Research Assistant", "Strategy", "RAG Assistant"),
    ("IT Service Desk Agent", "Technology", "Agentic AI"),
    ("Code Modernization Copilot", "Technology", "GenAI Copilot"),
    ("Collections Prioritization Model", "Finance", "Predictive ML"),
    ("Customer Churn Model", "Commercial", "Predictive ML"),
    ("Supplier Risk Monitor", "Procurement", "Predictive ML"),
    ("Revenue Assurance Agent", "Finance", "Agentic AI"),
    ("Knowledge Search Assistant", "Operations", "RAG Assistant"),
    ("Field Service Scheduling Agent", "Operations", "Agentic AI"),
    ("Employee Learning Copilot", "HR", "GenAI Copilot"),
    ("Regulatory Monitoring Assistant", "Compliance", "RAG Assistant"),
    ("Inventory Rebalancing Agent", "Supply Chain", "Agentic AI"),
    ("Customer Next-Best-Action Model", "Commercial", "Predictive ML"),
    ("Board Reporting Copilot", "Finance", "GenAI Copilot"),
]

STAGES = ["Concept", "Pilot", "Production"]


def _clamp(v: float, low: float = 0, high: float = 100) -> float:
    return float(max(low, min(high, v)))


def generate_portfolio(n: int = 24, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []

    for i, (name, function, ai_type) in enumerate(USE_CASES[:n], start=1):
        stage = rng.choice(STAGES, p=[0.25, 0.42, 0.33])
        revenue = int(rng.integers(50_000, 1_100_000))
        savings = int(rng.integers(40_000, 900_000))
        implementation_cost = int(rng.integers(80_000, 650_000))
        annual_run_cost = int(rng.integers(30_000, 320_000))

        autonomy = _clamp(rng.normal(72 if ai_type == "Agentic AI" else 38, 15))
        consequence = _clamp(rng.normal(64 if function in {"Finance", "Risk", "Legal", "Compliance"} else 48, 18))
        sensitivity = _clamp(rng.normal(67 if function in {"HR", "Finance", "Legal", "Risk"} else 45, 18))
        regulatory = _clamp(rng.normal(70 if function in {"Finance", "Legal", "Risk", "Compliance", "HR"} else 35, 20))
        model_uncertainty = _clamp(rng.normal(52 if "GenAI" in ai_type or "RAG" in ai_type or "Agentic" in ai_type else 34, 15))

        rows.append({
            "initiative_id": f"AI-{i:03d}",
            "initiative_name": name,
            "business_function": function,
            "ai_type": ai_type,
            "stage": stage,
            "executive_owner": rng.choice(["CFO", "COO", "CCO", "CTO", "CHRO", "CRO"]),
            "business_owner": f"{function} Director",
            "technical_owner": rng.choice(["AI Platform Team", "Data Science", "Enterprise Apps", "Digital Product"]),
            "revenue_uplift_eur": revenue,
            "cost_savings_eur": savings,
            "implementation_cost_eur": implementation_cost,
            "annual_run_cost_eur": annual_run_cost,
            "customer_impact": round(_clamp(rng.normal(62, 20)), 1),
            "strategic_alignment": round(_clamp(rng.normal(70, 16)), 1),
            "data_readiness": round(_clamp(rng.normal(61, 20)), 1),
            "technology_readiness": round(_clamp(rng.normal(64, 18)), 1),
            "organization_readiness": round(_clamp(rng.normal(55, 20)), 1),
            "skills_readiness": round(_clamp(rng.normal(58, 18)), 1),
            "autonomy": round(autonomy, 1),
            "consequence_severity": round(consequence, 1),
            "data_sensitivity": round(sensitivity, 1),
            "regulatory_exposure": round(regulatory, 1),
            "model_uncertainty": round(model_uncertainty, 1),
            "has_named_owner": bool(rng.choice([True, True, True, False])),
            "has_human_override": bool(rng.choice([True, True, False])),
            "has_audit_logging": bool(rng.choice([True, True, False])),
            "has_kill_switch": bool(rng.choice([True, False], p=[0.45, 0.55])) if ai_type == "Agentic AI" else True,
        })

    return pd.DataFrame(rows)


def write_sample_csv(path: str | Path, n: int = 24, seed: int = SEED) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_portfolio(n=n, seed=seed)
    df.to_csv(path, index=False)
    return path


if __name__ == "__main__":
    write_sample_csv(Path(__file__).resolve().parents[1] / "data" / "ai_portfolio.csv")
