"""Deterministic market data for the GENESIS 2026 simulation."""

STOCKS = [
    ("OMNA", "Omnia Cloud Systems", "Cloud Infrastructure", 320.0, 68.0),
    ("TMND", "TuringMind AI", "AI Compute / LLM", 180.0, 115.0),
    ("KVACH", "CyberKavach Infosec", "Cybersecurity Defense", 420.0, 54.0),
    ("VIST", "Vistara Tech Solutions", "IT Services & BPO", 850.0, 24.5),
    ("BCHIP", "Bharat Chip Foundry", "Semiconductor Fab", 380.0, 46.0),
    ("APEX", "Apex Capital & Trust", "Investment Banking", 540.0, 18.2),
    ("RVB", "Rashtriya Vikas Bank", "Public Sector Bank", 65.0, 6.8),
    ("CPBK", "Credence Private Bank", "Commercial Private Bank", 720.0, 19.5),
    ("VNTR", "VentureLeap Finance", "Startup & Venture Debt", 190.0, 38.0),
    ("PAYB", "PayBharat Digital", "Payments & FinTech", 95.0, 0.0),
    ("PLFE", "PureLife Consumer", "FMCG Personal Care", 450.0, 48.0),
    ("DAIRY", "DailyDairy Agro", "FMCG Dairy & Food", 180.0, 36.0),
    ("RBEV", "Royal Beverages Co.", "Discretionary Liquor", 820.0, 34.0),
    ("SANJ", "Sanjeevani Life Sciences", "Pharma Generics", 640.0, 27.0),
    ("GVAX", "GeneVax Therapeutics", "Biotech & Vaccines", 290.0, 42.0),
    ("MCRH", "MediCare Hospitals", "Hospital Chains", 980.0, 39.0),
    ("URJA", "Global Urja Power", "Thermal & Grid Utility", 110.0, 11.0),
    ("PIHC", "PetroInd Hydrocarbons", "Oil Refining & Petrochem", 340.0, 9.5),
    ("HSUN", "HelioSun Green Energy", "Solar & Wind Utility", 160.0, 62.0),
    ("VRID", "VoltRide Mobility", "EV Mobility", 75.0, 88.0),
    ("GATI", "Gati Motors Ltd.", "Commercial & Passenger", 480.0, 16.0),
    ("GARU", "Garuda Airlines", "Domestic Aviation", 210.0, 28.0),
    ("SETU", "Setu Infrastructure", "Roads & Civil EPC", 310.0, 14.5),
    ("SKYL", "Skylark Urban Realty", "Real Estate Development", 280.0, 31.0),
    ("KSTL", "Kalinga Steel & Iron", "Primary Steel Mills", 145.0, 7.8),
    ("BCTC", "Bharat Connect Telecom", "5G Network Carrier", 260.0, 29.0),
    ("STMW", "StreamWave Entertainment", "OTT Streaming & Gaming", 195.0, 44.0),
    ("QDRP", "QuickDrop Logistics", "E-Commerce Express Cargo", 230.0, 33.0),
    ("BZAR", "BazaarDirect Retail", "Hypermarket Chains", 680.0, 35.0),
    ("TRSH", "Trishul Defense Systems", "Defense Electronics", 520.0, 32.0),
]

_DEFAULT = {symbol: 0.0 for symbol, *_ in STOCKS}


def _deltas(**values: float) -> dict[str, float]:
    result = _DEFAULT.copy()
    result.update(values)
    return result


SCENARIOS = {
    "ERA_1_DOT_COM": ("The Silicon Vapor Implosion", "Tech multiples crash; defensive staples rotate higher.", _deltas(TMND=-.65, PAYB=-.62, OMNA=-.55, VRID=-.48, BCHIP=-.45, KVACH=-.40, STMW=-.38, VNTR=-.42, PLFE=.08, DAIRY=.06, SANJ=.05)),
    "ERA_2_CAPEX": ("The Capex Supercycle", "Infrastructure and industrial investment accelerate.", _deltas(KSTL=.55, SETU=.48, BCHIP=.42, URJA=.35, GATI=.28, SKYL=.22, TMND=-.12, PAYB=-.10)),
    "ERA_3_GFC_2008": ("The Global Credit Crisis", "Leverage unwinds and financials lead the crash.", _deltas(VNTR=-.68, SKYL=-.58, APEX=-.52, CPBK=-.45, RVB=-.38, PAYB=-.40, PLFE=.12, SANJ=.10)),
    "ERA_4_QE_STIMULUS": ("The Liquidity Boom", "Stimulus reflates credit, auto and financial assets.", _deltas(CPBK=.38, GATI=.35, APEX=.30, SKYL=.28, SETU=.25, VNTR=.22, RVB=.20, SANJ=-.08)),
    "ERA_5_CRUDE_CRASH": ("The Crude Collapse", "Lower fuel costs benefit airlines and consumers.", _deltas(GARU=.42, RBEV=.20, BZAR=.18, DAIRY=.15, PIHC=-.45, URJA=-.15, SETU=.12)),
    "ERA_6_DIGITAL_EV": ("The Digital and EV Boom", "FinTech, AI and mobility attract fresh capital.", _deltas(VRID=.65, PAYB=.55, TMND=.48, BCHIP=.45, OMNA=.40, BCTC=.30, PIHC=-.20)),
    "ERA_7_COVID_19": ("The COVID-19 Shock", "Healthcare and cloud surge while travel collapses.", _deltas(GVAX=.68, OMNA=.45, TMND=.35, SANJ=.30, GARU=-.62, RBEV=-.35, BZAR=-.25, PIHC=-.20)),
    "ERA_8_SUPPLY_BOTTLENECKS": ("The Supply Chokepoints", "Foundries, cargo and industrial capacity command a premium.", _deltas(BCHIP=.52, KSTL=.44, QDRP=.38, SETU=.30, URJA=.25, GARU=.18, BZAR=-.18, PAYB=-.12)),
    "ERA_9_AI_SUPERCYCLE": ("The AI Supercycle", "AI compute monopolies dominate risk appetite.", _deltas(TMND=.85, BCHIP=.48, OMNA=.45, KVACH=.38, STMW=.30, VIST=.25, PLFE=-.10, GARU=-.12)),
    "ERA_10_YAPOO_59": ("YAPOO 59 - The Blackout Protocol", "A universal cyber-biological shock collapses risk assets.", _deltas(TMND=-.85, PAYB=-.80, VRID=-.78, OMNA=-.75, STMW=-.72, KVACH=-.70, VNTR=-.68, HSUN=-.68, GARU=-.65, BCHIP=-.65, SKYL=-.62, QDRP=-.60, GATI=-.52, APEX=-.48, SETU=-.48, PLFE=-.24, DAIRY=-.22, SANJ=-.25, TRSH=-.18, RVB=-.18)),
}

