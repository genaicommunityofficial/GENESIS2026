"""In-memory peace-time jitter (PRD §7). NO database writes here."""
import asyncio, logging, random
from ..state import app_state
from ..core.config import settings
from .ws_manager import ws_manager
from .trading import forced_cover_scan

log = logging.getLogger("tick")

def next_price(price: float, anchor: float, sigma: float, k: float = 0.15) -> float:
    # PRD formula with the anchor gap normalised to a fraction (PRD mixes ₹ and %)
    dp = price * (sigma * random.gauss(0, 1) - k * (price - anchor) / anchor)
    return max(settings.price_floor, round(price + dp, 2))

async def _tick_once(pool):
    if not app_state.ticks_enabled or not app_state.prices: return
    for sym in app_state.prices:
        app_state.prices[sym] = next_price(app_state.prices[sym], app_state.anchors[sym], app_state.sigma[sym])
    await ws_manager.broadcast({"type": "PRICE_UPDATE", "prices": app_state.prices})
    await forced_cover_scan(pool)

async def supervisor(pool):
    """Self-healing loop: an exception never kills the task."""
    while True:
        try:
            while True:
                await _tick_once(pool)
                await asyncio.sleep(random.uniform(settings.tick_min_s, settings.tick_max_s))
        except asyncio.CancelledError: raise
        except Exception:
            log.exception("tick worker crashed; restarting in 5s")
            await asyncio.sleep(5)
