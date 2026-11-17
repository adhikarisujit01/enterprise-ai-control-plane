from pathlib import Path
import pandas as pd

from src.scoring import score_portfolio
from src.governance import add_governance_controls
from src.recommendations import add_recommendations
from src.scenario import run_portfolio_scenario, scenario_delta
from src.roadmap import build_transformation_roadmap


def _base():
    path = Path(__file__).parents[1] / "data" / "ai_portfolio.csv"
    raw = pd.read_csv(path)
    return raw, add_recommendations(add_governance_controls(score_portfolio(raw)))


def test_benefit_stress_reduces_value():
    raw, baseline = _base()
    stressed = run_portfolio_scenario(raw, benefit_realization=0.6)
    assert stressed["steady_state_net_value_eur"].sum() < baseline["steady_state_net_value_eur"].sum()


def test_scenario_delta_flags_changes():
    raw, baseline = _base()
    stressed = run_portfolio_scenario(raw, benefit_realization=0.35, implementation_cost_multiplier=1.5)
    delta = scenario_delta(baseline, stressed)
    assert "decision_changed" in delta.columns
    assert len(delta) == len(baseline)


def test_roadmap_has_every_initiative():
    _, baseline = _base()
    roadmap = build_transformation_roadmap(baseline)
    assert len(roadmap) == len(baseline)
    assert roadmap["next_step"].str.len().min() > 20
