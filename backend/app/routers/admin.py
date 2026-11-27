from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from ..core import db
from ..core.security import require_admin
from ..state import app_state
from ..services import scenarios
from ..services.ws_manager import ws_manager
from ..services.leaderboard import compute_rankings
from ..core.config import settings

router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])

class ScenarioIn(BaseModel):
    scenario_id: str

@router.post("/scenario/trigger")
async def trigger(body: ScenarioIn, admin=Depends(require_admin)):
    async with db.pool.acquire() as conn:
        await scenarios.execute_era(conn, body.scenario_id, admin["sub"], db.pool)
    return {"ok": True}

@router.patch("/market/pause")
async def pause():
    app_state.market_open = not app_state.market_open
    async with db.pool.acquire() as c:
        await c.execute("UPDATE market_settings SET is_market_open=$1 WHERE id=1", app_state.market_open)
    await ws_manager.broadcast({"type": "MARKET_STATUS", "open": app_state.market_open})
    return {"open": app_state.market_open}

@router.patch("/ticks/toggle")
async def toggle_ticks():
    app_state.ticks_enabled = not app_state.ticks_enabled
    return {"ticks_enabled": app_state.ticks_enabled}

@router.post("/leaderboard/freeze")
async def freeze():
    async with db.pool.acquire() as c:
        app_state.leaderboard_cache = await compute_rankings(c)
        await c.execute("INSERT INTO leaderboard_snapshot(id,payload,taken_at) VALUES(1,$1::jsonb,NOW()) ON CONFLICT(id) DO UPDATE SET payload=EXCLUDED.payload,taken_at=NOW()", __import__("json").dumps(app_state.leaderboard_cache))
        await c.execute("UPDATE market_settings SET is_leaderboard_frozen=TRUE WHERE id=1")
    app_state.leaderboard_frozen = True
    return {"frozen": True}

@router.post("/leaderboard/reveal")
async def reveal():
    app_state.leaderboard_frozen = False
    async with db.pool.acquire() as c:
        await c.execute("UPDATE market_settings SET is_leaderboard_frozen=FALSE WHERE id=1")
    return {"frozen": False}

@router.post("/prices/force-sync")
async def force_sync():
    app_state.prices.update(app_state.anchors)
    async with db.pool.acquire() as c:
        for sym, price in app_state.prices.items():
            await c.execute("UPDATE stocks SET current_price=$1,last_updated=NOW() WHERE company_id=$2", price, app_state.company_id[sym])
    await ws_manager.broadcast({"type": "PRICE_UPDATE", "prices": app_state.prices})
    return {"ok": True}

@router.get("/users/pending")
async def pending_users():
    async with db.pool.acquire() as c:
        rows = await c.fetch("SELECT id,full_name,email,reg_number,created_at FROM profiles WHERE role='PARTICIPANT' AND status='PENDING' ORDER BY created_at")
    return [dict(r) for r in rows]

@router.post("/users/{user_id}/approve")
async def approve_user(user_id: UUID, admin=Depends(require_admin)):
    async with db.pool.acquire() as c:
        async with c.transaction():
            row = await c.fetchrow("UPDATE profiles SET status='ACTIVE' WHERE id=$1 AND role='PARTICIPANT' AND status='PENDING' RETURNING id", user_id)
            if not row: raise HTTPException(404, "Pending participant not found")
            await c.execute("INSERT INTO wallets(user_id) VALUES($1) ON CONFLICT(user_id) DO NOTHING", row["id"])
            await c.execute("INSERT INTO audit_log(actor_id,action,detail) VALUES($1,'USER_APPROVED',$2::jsonb)", admin["sub"], __import__("json").dumps({"user_id": str(user_id)}))
    return {"status": "ACTIVE"}

@router.post("/users/{user_id}/reject")
async def reject_user(user_id: UUID, admin=Depends(require_admin)):
    async with db.pool.acquire() as c:
        result = await c.execute("UPDATE profiles SET status='REJECTED' WHERE id=$1 AND role='PARTICIPANT' AND status='PENDING'", user_id)
        if result.endswith("0"): raise HTTPException(404, "Pending participant not found")
        await c.execute("INSERT INTO audit_log(actor_id,action,detail) VALUES($1,'USER_REJECTED',$2::jsonb)", admin["sub"], __import__("json").dumps({"user_id": str(user_id)}))
    return {"status": "REJECTED"}

@router.get("/topups")
async def topups():
    async with db.pool.acquire() as c:
        rows = await c.fetch("SELECT t.id,t.user_id,p.full_name,p.email,t.status,t.created_at FROM topup_requests t JOIN profiles p ON p.id=t.user_id ORDER BY t.created_at DESC")
    return [dict(r) for r in rows]

@router.post("/topups/{request_id}/{decision}")
async def decide_topup(request_id: int, decision: str, admin=Depends(require_admin)):
    if decision not in {"approve", "reject"}: raise HTTPException(422, "Decision must be approve or reject")
    async with db.pool.acquire() as c:
        async with c.transaction():
            req = await c.fetchrow("SELECT * FROM topup_requests WHERE id=$1 FOR UPDATE", request_id)
            if not req or req["status"] != "PENDING": raise HTTPException(404, "Pending request not found")
            status = "APPROVED" if decision == "approve" else "REJECTED"
            await c.execute("UPDATE topup_requests SET status=$1,decided_by=$2,decided_at=NOW() WHERE id=$3", status, admin["sub"], request_id)
            if decision == "approve":
                await c.execute("UPDATE wallets SET balance=balance+$1,total_credited=total_credited+$1,updated_at=NOW() WHERE user_id=$2", settings.topup_amount, req["user_id"])
            await c.execute("INSERT INTO audit_log(actor_id,action,detail) VALUES($1,$2,$3::jsonb)", admin["sub"], f"TOPUP_{status}", __import__("json").dumps({"request_id": request_id}))
    return {"status": status}

@router.get("/leaderboard")
async def admin_leaderboard(): return app_state.admin_live

@router.get("/audit")
async def audit():
    async with db.pool.acquire() as c:
        rows = await c.fetch("SELECT a.id,a.action,a.detail,a.created_at,p.full_name AS actor FROM audit_log a LEFT JOIN profiles p ON p.id=a.actor_id ORDER BY a.created_at DESC LIMIT 100")
    return [dict(r) for r in rows]
