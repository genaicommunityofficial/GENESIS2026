import json
from fastapi import HTTPException
from ..scenarios_config import deltas_for, ERAS
from ..state import app_state
from ..core.config import settings
from .ws_manager import ws_manager
from .trading import forced_cover_scan

async def execute_era(conn, scenario_id: str, admin_id: str, pool):
    try: deltas = deltas_for(scenario_id)
    except ValueError: raise HTTPException(404, "Unknown era")

    next_prices = {}
    async with app_state.trade_lock:
      async with conn.transaction():
        completed = await conn.fetchval("SELECT COUNT(*) FROM scenario_executions")
        expected = ERAS[completed][0] if completed < len(ERAS) else None
        if scenario_id != expected:
            raise HTTPException(409, f"Next era must be {expected or 'none; all eras are complete'}")
        # idempotency: UNIQUE(scenario_id) makes a double-click fail
        ok = await conn.fetchval(
            "INSERT INTO scenario_executions(scenario_id, executed_by) VALUES($1,$2) "
            "ON CONFLICT DO NOTHING RETURNING id", scenario_id, admin_id)
        if not ok: raise HTTPException(409, "Era already executed")

        for sym, d in deltas.items():
            if sym not in app_state.prices:
                raise HTTPException(503, f"Price data missing for {sym}")
            new = max(settings.price_floor, round(app_state.prices[sym] * (1 + d), 2))
            await conn.execute("UPDATE stocks SET current_price=$1,anchor_price=$1,day_high=$1,day_low=$1,last_updated=NOW() WHERE company_id=$2", new, app_state.company_id[sym])
            next_prices[sym] = new
        await conn.execute("UPDATE market_settings SET active_scenario_name=$1 WHERE id=1", scenario_id)
        await conn.execute("INSERT INTO audit_log(actor_id,action,detail) VALUES($1,'ERA_EXECUTED',$2::jsonb)",
                           admin_id, json.dumps({"scenario": scenario_id}))
      app_state.prices.update(next_prices)
      app_state.anchors.update(next_prices)
    await forced_cover_scan(pool)
    await ws_manager.broadcast({"type": "ERA_TRIGGERED", "scenario": scenario_id, "prices": app_state.prices})
