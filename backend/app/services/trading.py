"""Atomic dealer execution and portfolio accounting."""
from fastapi import HTTPException
from ..state import app_state
from ..core.config import settings


def net_worth(cash, collateral, longs, shorts) -> float:
    return float(cash) + sum(q * p for q, p in longs) + float(collateral) - sum(q * p for q, p in shorts)


def check_squeeze(entry_price: float, current_price: float) -> bool:
    return current_price >= settings.short_squeeze_mult * entry_price


async def _position(conn, user_id, company_id, side):
    return await conn.fetchrow("SELECT * FROM holdings WHERE user_id=$1 AND company_id=$2 AND side=$3 FOR UPDATE", user_id, company_id, side)


async def _portfolio_value(conn, user_id):
    wallet = await conn.fetchrow("SELECT * FROM wallets WHERE user_id=$1", user_id)
    rows = await conn.fetch("SELECT h.side,h.quantity,h.avg_entry_price,c.symbol FROM holdings h JOIN companies c ON c.id=h.company_id WHERE h.user_id=$1", user_id)
    longs, shorts = [], []
    for r in rows:
        price = app_state.prices.get(r["symbol"], 0)
        (longs if r["side"] == "LONG" else shorts).append((r["quantity"], price))
    return wallet, net_worth(wallet["balance"], wallet["collateral_locked"], longs, shorts)


async def place_order(conn, user_id: str, company_id: str, action: str, qty: int) -> dict:
    if not app_state.market_open:
        raise HTTPException(423, "Market is paused")
    if qty <= 0:
        raise HTTPException(422, "Quantity must be greater than zero")
    symbol = app_state.symbol_by_company.get(str(company_id))
    if symbol is None:
        raise HTTPException(404, "Company not found")
    price = round(float(app_state.prices[symbol]), 2)
    async with app_state.trade_lock:
        async with conn.transaction():
            wallet = await conn.fetchrow("SELECT * FROM wallets WHERE user_id=$1 FOR UPDATE", user_id)
            if not wallet:
                raise HTTPException(409, "Wallet has not been created")
            long_pos = await _position(conn, user_id, company_id, "LONG")
            short_pos = await _position(conn, user_id, company_id, "SHORT")
            total_symbol_qty = (long_pos["quantity"] if long_pos else 0) + (short_pos["quantity"] if short_pos else 0)
            realized = 0.0
            amount = round(qty * price, 2)

            if action in ("BUY", "SHORT") and total_symbol_qty + qty > settings.max_shares_per_user:
                raise HTTPException(422, f"Maximum {settings.max_shares_per_user} shares per company")
            if action == "BUY":
                if short_pos:
                    raise HTTPException(422, "Cover the short position before opening a long position")
                if wallet["balance"] < amount:
                    raise HTTPException(422, "Insufficient free cash")
                _, worth = await _portfolio_value(conn, user_id)
                current_value = (long_pos["quantity"] * price if long_pos else 0) + amount
                if worth <= 0 or current_value > worth * settings.max_concentration_pct:
                    raise HTTPException(422, "Order exceeds the 35% single-stock concentration limit")
                if long_pos:
                    total_qty = long_pos["quantity"] + qty
                    avg = (long_pos["quantity"] * float(long_pos["avg_entry_price"]) + amount) / total_qty
                    await conn.execute("UPDATE holdings SET quantity=$1,avg_entry_price=$2,updated_at=NOW() WHERE id=$3", total_qty, avg, long_pos["id"])
                else:
                    await conn.execute("INSERT INTO holdings(user_id,company_id,side,quantity,avg_entry_price) VALUES($1,$2,'LONG',$3,$4)", user_id, company_id, qty, price)
                await conn.execute("UPDATE wallets SET balance=balance-$1,updated_at=NOW() WHERE user_id=$2", amount, user_id)
            elif action == "SELL":
                if not long_pos or long_pos["quantity"] < qty:
                    raise HTTPException(422, "Not enough shares to sell")
                realized = round(qty * (price - float(long_pos["avg_entry_price"])), 2)
                if long_pos["quantity"] == qty:
                    await conn.execute("DELETE FROM holdings WHERE id=$1", long_pos["id"])
                else:
                    await conn.execute("UPDATE holdings SET quantity=quantity-$1,updated_at=NOW() WHERE id=$2", qty, long_pos["id"])
                await conn.execute("UPDATE wallets SET balance=balance+$1,updated_at=NOW() WHERE user_id=$2", amount, user_id)
            elif action == "SHORT":
                if long_pos:
                    raise HTTPException(422, "Sell the long position before opening a short position")
                if wallet["balance"] < amount:
                    raise HTTPException(422, "Insufficient free cash for 100% short collateral")
                _, worth = await _portfolio_value(conn, user_id)
                current_value = (short_pos["quantity"] * price if short_pos else 0) + amount
                if worth <= 0 or current_value > worth * settings.max_concentration_pct:
                    raise HTTPException(422, "Order exceeds the 35% single-stock concentration limit")
                if short_pos:
                    total_qty = short_pos["quantity"] + qty
                    avg = (short_pos["quantity"] * float(short_pos["avg_entry_price"]) + amount) / total_qty
                    await conn.execute("UPDATE holdings SET quantity=$1,avg_entry_price=$2,updated_at=NOW() WHERE id=$3", total_qty, avg, short_pos["id"])
                else:
                    await conn.execute("INSERT INTO holdings(user_id,company_id,side,quantity,avg_entry_price) VALUES($1,$2,'SHORT',$3,$4)", user_id, company_id, qty, price)
                # Reserve the trader's 100% margin and hold the short-sale proceeds.
                await conn.execute("UPDATE wallets SET balance=balance-$1,collateral_locked=collateral_locked+$2,updated_at=NOW() WHERE user_id=$3", amount, amount * 2, user_id)
            elif action == "COVER":
                if not short_pos or short_pos["quantity"] < qty:
                    raise HTTPException(422, "Not enough short shares to cover")
                entry = float(short_pos["avg_entry_price"])
                released = round(qty * entry * 2, 2)
                realized = round(qty * (entry - price), 2)
                payout = max(0.0, round(released - amount, 2))
                if short_pos["quantity"] == qty:
                    await conn.execute("DELETE FROM holdings WHERE id=$1", short_pos["id"])
                else:
                    await conn.execute("UPDATE holdings SET quantity=quantity-$1,updated_at=NOW() WHERE id=$2", qty, short_pos["id"])
                await conn.execute("UPDATE wallets SET balance=balance+$1,collateral_locked=collateral_locked-$2,updated_at=NOW() WHERE user_id=$3", payout, released, user_id)
            else:
                raise HTTPException(422, "Invalid order action")

            await conn.execute("INSERT INTO transactions(user_id,company_id,side,quantity,price,realized_pnl) VALUES($1,$2,$3,$4,$5,$6)", user_id, company_id, action, qty, price, realized)
    return {"status": "FILLED", "symbol": symbol, "action": action, "quantity": qty, "price": price, "total": amount, "realized_pnl": realized}


async def forced_cover_scan(pool):
    """Close shorts when price reaches 1.8x entry; run after price changes."""
    async with app_state.trade_lock:
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT h.*,c.symbol FROM holdings h JOIN companies c ON c.id=h.company_id WHERE h.side='SHORT'")
            for row in rows:
                price = app_state.prices.get(row["symbol"])
                if price is None or not check_squeeze(float(row["avg_entry_price"]), price):
                    continue
                async with conn.transaction():
                    wallet = await conn.fetchrow("SELECT * FROM wallets WHERE user_id=$1 FOR UPDATE", row["user_id"])
                    qty = row["quantity"]
                    released = round(qty * float(row["avg_entry_price"]) * 2, 2)
                    pnl = round(qty * (float(row["avg_entry_price"]) - price), 2)
                    payout = max(0.0, round(released - qty * price, 2))
                    await conn.execute("DELETE FROM holdings WHERE id=$1", row["id"])
                    await conn.execute("UPDATE wallets SET balance=balance+$1,collateral_locked=collateral_locked-$2,updated_at=NOW() WHERE user_id=$3", payout, released, row["user_id"])
                    await conn.execute("INSERT INTO transactions(user_id,company_id,side,quantity,price,realized_pnl,forced) VALUES($1,$2,'COVER',$3,$4,$5,TRUE)", row["user_id"], row["company_id"], qty, price, pnl)
