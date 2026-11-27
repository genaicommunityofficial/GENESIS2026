import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .core import db
from .core.config import settings
from .state import app_state
from .routers import auth, trade, admin, leaderboard
from .services.ws_manager import ws_manager
from .services.tick_engine import supervisor
from .services.leaderboard import leaderboard_loop

async def load_prices():
    async with db.pool.acquire() as c:
        rows = await c.fetch("SELECT c.id, c.symbol, s.current_price, s.anchor_price "
                             "FROM companies c JOIN stocks s ON s.company_id=c.id")
    for r in rows:
        sym = r["symbol"]
        app_state.prices[sym] = float(r["current_price"])
        app_state.anchors[sym] = float(r["anchor_price"])
        app_state.company_id[sym] = str(r["id"])
        app_state.symbol_by_company[str(r["id"])] = sym
        app_state.sigma[sym] = 0.003 if sym in {"OMNA", "TMND", "VRID", "PAYB", "STMW", "KVACH"} else 0.001

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    await load_prices()
    async with db.pool.acquire() as c:
        row = await c.fetchrow("SELECT is_market_open, is_leaderboard_frozen FROM market_settings WHERE id=1")
        if row:
            app_state.market_open = row["is_market_open"]
            app_state.leaderboard_frozen = row["is_leaderboard_frozen"]
        snapshot = await c.fetchval("SELECT payload FROM leaderboard_snapshot WHERE id=1")
        if snapshot:
            app_state.leaderboard_cache = json.loads(snapshot) if isinstance(snapshot, str) else snapshot
    tasks = [asyncio.create_task(supervisor(db.pool)), asyncio.create_task(leaderboard_loop(db.pool))]
    yield
    for t in tasks: t.cancel()
    await db.close_pool()

app = FastAPI(title="GENESIS 2026", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","),
                   allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, trade.router, admin.router, leaderboard.router): app.include_router(r)

@app.get("/api/health")
async def health():
    return {"ok": True, "ticks": app_state.ticks_enabled, "market_open": app_state.market_open}

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    from .core.security import decode_token
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4401); return
    try:
        decode_token(token)
    except Exception:
        await ws.close(code=4401); return
    await ws_manager.connect(ws)
    try:
        while True:
            msg = await ws.receive_json()
            if msg.get("type") == "PING": await ws.send_json({"type": "PONG"})
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
