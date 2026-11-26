from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal
from ..core import db
from ..core.security import require_participant
from ..services import trading
from ..state import app_state

router = APIRouter(prefix="/api/v1", tags=["trade"])

class OrderIn(BaseModel):
    company_id: str
    action: Literal["BUY", "SELL", "SHORT", "COVER"]
    qty: int

@router.post("/trade/order")
async def order(body: OrderIn, user=Depends(require_participant)):
    async with db.pool.acquire() as conn:
        return await trading.place_order(conn, user["sub"], body.company_id, body.action, body.qty)

@router.get("/portfolio/me")
async def portfolio(user=Depends(require_participant)):
    async with db.pool.acquire() as conn:
        wallet = await conn.fetchrow("SELECT * FROM wallets WHERE user_id=$1", user["sub"])
        rows = await conn.fetch("SELECT h.side,h.quantity,h.avg_entry_price,c.id AS company_id,c.name,c.symbol,c.sector FROM holdings h JOIN companies c ON c.id=h.company_id WHERE h.user_id=$1 ORDER BY c.symbol", user["sub"])
        transactions = await conn.fetch("SELECT t.side,t.quantity,t.price,t.realized_pnl,t.forced,t.created_at,c.symbol FROM transactions t JOIN companies c ON c.id=t.company_id WHERE t.user_id=$1 ORDER BY t.created_at DESC LIMIT 20", user["sub"])
    positions=[]; longs=[]; shorts=[]; unrealized=0.0
    for r in rows:
        current=app_state.prices.get(r["symbol"], float(r["avg_entry_price"]))
        qty=int(r["quantity"]); entry=float(r["avg_entry_price"])
        pnl=round(qty*(current-entry if r["side"]=="LONG" else entry-current),2)
        unrealized += pnl
        positions.append({"company_id":str(r["company_id"]),"name":r["name"],"symbol":r["symbol"],"sector":r["sector"],"side":r["side"],"quantity":qty,"avg_entry_price":entry,"current_price":current,"market_value":round(qty*current,2),"unrealized_pnl":pnl})
        (longs if r["side"]=="LONG" else shorts).append((qty,current))
    worth=trading.net_worth(float(wallet["balance"]),float(wallet["collateral_locked"]),longs,shorts)
    return {"balance":float(wallet["balance"]),"collateral_locked":float(wallet["collateral_locked"]),"total_credited":float(wallet["total_credited"]),"net_worth":round(worth,2),"unrealized_pnl":round(unrealized,2),"positions":positions,"transactions":[dict(r) for r in transactions]}

@router.get("/stocks")
async def stocks():
    async with db.pool.acquire() as c:
        rows=await c.fetch("SELECT c.id,c.name,c.symbol,c.sector,c.pe_ratio,s.current_price,s.anchor_price,s.day_high,s.day_low FROM companies c JOIN stocks s ON s.company_id=c.id ORDER BY c.symbol")
    return [{"id":str(r["id"]),"name":r["name"],"symbol":r["symbol"],"sector":r["sector"],"pe_ratio":float(r["pe_ratio"]) if r["pe_ratio"] is not None else None,"price":app_state.prices.get(r["symbol"],float(r["current_price"])),"anchor_price":app_state.anchors.get(r["symbol"],float(r["anchor_price"])),"day_high":float(r["day_high"]),"day_low":float(r["day_low"])} for r in rows]

@router.post("/topup/request")
async def request_topup(user=Depends(require_participant)):
    async with db.pool.acquire() as c:
        try: await c.execute("INSERT INTO topup_requests(user_id) VALUES($1)", user["sub"])
        except Exception as exc:
            if "unique" in str(exc).lower(): raise HTTPException(409,"A top-up request has already been submitted")
            raise
    return {"status": "PENDING"}

@router.get("/transactions/me")
async def my_transactions(user=Depends(require_participant)):
    async with db.pool.acquire() as c:
        rows=await c.fetch("SELECT t.id,t.side,t.quantity,t.price,t.realized_pnl,t.forced,t.created_at,c.symbol FROM transactions t JOIN companies c ON c.id=t.company_id WHERE t.user_id=$1 ORDER BY t.created_at DESC LIMIT 100",user["sub"])
    return [dict(r) for r in rows]
