"""Batch job: compute net worth for all ACTIVE users every ~3s and cache it. Never recompute per request."""
import asyncio
from ..state import app_state
from .ws_manager import ws_manager

async def compute_rankings(conn) -> list[dict]:
    rows = await conn.fetch("SELECT p.id,p.full_name,p.email,w.balance,w.collateral_locked,w.total_credited,h.side,h.quantity,c.symbol FROM profiles p JOIN wallets w ON w.user_id=p.id LEFT JOIN holdings h ON h.user_id=p.id LEFT JOIN companies c ON c.id=h.company_id WHERE p.role='PARTICIPANT' AND p.status='ACTIVE' ORDER BY p.id")
    totals = {}
    for r in rows:
        uid = str(r["id"])
        item = totals.setdefault(uid, {"name": r["full_name"], "cash": float(r["balance"]), "collateral": float(r["collateral_locked"]), "credited": float(r["total_credited"]), "longs": 0.0, "shorts": 0.0})
        if r["symbol"]:
            value = int(r["quantity"]) * app_state.prices.get(r["symbol"], 0)
            item["longs" if r["side"] == "LONG" else "shorts"] += value
    ranking = []
    for item in totals.values():
        worth = item["cash"] + item["collateral"] + item["longs"] - item["shorts"]
        ranking.append({"name": item["name"], "net_worth": round(worth, 2), "pnl": round(worth - item["credited"], 2), "pnl_pct": round((worth / item["credited"] - 1) * 100, 2) if item["credited"] else 0})
    ranking.sort(key=lambda x: x["net_worth"], reverse=True)
    for rank, item in enumerate(ranking, 1): item["rank"] = rank
    return ranking

async def leaderboard_loop(pool):
    while True:
        try:
            async with pool.acquire() as conn:
                ranks = await compute_rankings(conn)
            app_state.admin_live = ranks
            if not app_state.leaderboard_frozen:
                app_state.leaderboard_cache = ranks
            # The socket is shared with participants; never leak live ranks while frozen.
            await ws_manager.broadcast({"type": "RANK_UPDATE", "ranks": app_state.leaderboard_cache})
        except Exception:
            import logging
            logging.getLogger("leaderboard").exception("leaderboard refresh failed")
        await asyncio.sleep(3)
