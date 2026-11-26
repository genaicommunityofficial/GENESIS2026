"""Single-process RAM state. Requires uvicorn --workers 1."""
from dataclasses import dataclass, field
import asyncio

@dataclass
class AppState:
    prices: dict[str, float] = field(default_factory=dict)    # symbol -> current price
    anchors: dict[str, float] = field(default_factory=dict)   # symbol -> anchor (era base) price
    sigma: dict[str, float] = field(default_factory=dict)     # symbol -> jitter volatility
    company_id: dict[str, str] = field(default_factory=dict)  # symbol -> uuid
    symbol_by_company: dict[str, str] = field(default_factory=dict)
    market_open: bool = False
    ticks_enabled: bool = True
    leaderboard_frozen: bool = False
    leaderboard_cache: list = field(default_factory=list)     # what participants see
    admin_live: list = field(default_factory=list)            # what admins see
    trade_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

app_state = AppState()
