from app.scenarios_config import DELTAS_PCT, deltas_for
from app.companies_seed import COMPANIES

def test_30_stocks_10_eras():
    assert len(DELTAS_PCT) == 30 and len(COMPANIES) == 30
    assert all(len(v) == 10 for v in DELTAS_PCT.values())
    assert {c[0] for c in COMPANIES} == set(DELTAS_PCT)

def test_yapoo_every_stock_drops():
    assert all(v[9] < 0 for v in DELTAS_PCT.values())

def test_spot_checks_against_prd():
    assert deltas_for("ERA_1_DOT_COM")["TMND"] == -0.65
    assert deltas_for("ERA_9_AI")["TMND"] == 0.85
    assert deltas_for("ERA_7_COVID")["GARU"] == -0.62
