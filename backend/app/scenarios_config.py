"""
HARDCODED era deltas (PRD §6). Percent values; each list = E1..E10.
Never edit at runtime. Verified by tests/test_scenarios.py.
"""
ERAS = [
 ("ERA_1_DOT_COM",  "Dot-Com Bubble Crash"),
 ("ERA_2_CAPEX",    "Global Capex & Infra Boom"),
 ("ERA_3_GFC",      "Lehman / GFC Crash"),
 ("ERA_4_QE",       "Zero Rates & QE Boom"),
 ("ERA_5_CRUDE",    "OPEC Oil Price War"),
 ("ERA_6_DIGITAL",  "4G Mobile & EV Boom"),
 ("ERA_7_COVID",    "COVID-19 Lockdowns"),
 ("ERA_8_SUPPLY",   "Post-Lockdown Supply Squeeze"),
 ("ERA_9_AI",       "Generative AI Boom"),
 ("ERA_10_YAPOO59", "YAPOO 59 Blackout"),
]

#            E1   E2   E3   E4   E5   E6   E7   E8   E9  E10
DELTAS_PCT = {
 "OMNA": [-55, 14,-30, 15,  2,  42, 38, -6, 35,-75],
 "TMND": [-65,  8,-35, 10, -4,  35, 35, -8, 85,-85],
 "KVACH":[-40,  8,-25, 12, -2,  28, 20,  4, 30,-70],
 "VIST": [-18, 12,-18, 12,  4,  18, 15,  2,-14,-45],
 "BCHIP":[-45, 15,-32, 14,  2,  22, 10, 52, 48,-65],
 "APEX": [-22, 20,-38, 30, -6,  10,-12, 18,  8,-48],
 "RVB":  [-10, 32,-18, 28,-12,   6, -8, 16,  4,-18],
 "CPBK": [-16, 22,-32, 38,  5,  12,-10, 14, 12,-42],
 "VNTR": [-42, 15,-68, 22,-14,  20,-22, 10, 25,-68],
 "PAYB": [-62, 10,-62, 18,  4,  55, 28,  8, 18,-80],
 "PLFE": [ -6,  5, -4,  8, 18,   2, 12,-10, -6,-24],
 "DAIRY":[ -5,  4, -2,  6, 15,   1,  8, -8, -5,-22],
 "RBEV": [-12, 10,-15, 22, 15,   6,-18,-12,  5,-38],
 "SANJ": [ -4,  6,  2,  8,  6,   4, 52,  4,  2,-25],
 "GVAX": [-12,  5,-10, 10, -4,   5, 68,  2,  8,-55],
 "MCRH": [ -5,  6,  1,  8,  5,   4, 42,  2,  4,-28],
 "URJA": [ -6, 25, -6, 10,-15,  -2, -2,  4, -6,-22],
 "PIHC": [-12, 38,-24, 16,-45,   4,-32, 30,  6,-45],
 "HSUN": [-32, 20,-42, 18,-35,  15, 15,  8, 18,-68],
 "VRID": [-48, 12,-45, 15, -8,  65, 20, 15, 38,-78],
 "GATI": [-18, 24,-32, 35,  8,   8,-54, 25, 12,-52],
 "GARU": [-16, 18,-35, 18, 42,   6,-62, 28, 10,-65],
 "SETU": [-15, 48,-28, 32,-10,   6,-15, 24, 15,-48],
 "SKYL": [-20, 42,-58, 25, -8,   5,-42, 20, 14,-62],
 "KSTL": [-14, 55,-34, 18,-28,   4,-18, 44, 12,-42],
 "BCTC": [ -7, 10, -8, 12,  6,  45, 18,  6,  8,-32],
 "STMW": [-38,  8,-14, 14,  2,  38, 36,-12, 16,-72],
 "QDRP": [-30, 15,-22, 18, 28,  25, 32, 35, 14,-60],
 "BZAR": [ -8, 12,-12, 20, 12,  14, 14,  6,  5,-32],
 "TRSH": [ -4, 10,  2,  8,  5,   4, -2,  6, 15,-18],
}

def deltas_for(scenario_id: str) -> dict[str, float]:
    """Return {symbol: fraction}, e.g. -0.65. Raises ValueError for unknown era."""
    idx = [e[0] for e in ERAS].index(scenario_id)
    return {sym: row[idx] / 100.0 for sym, row in DELTAS_PCT.items()}
