"""FastAPI service for the GENESIS 2026 virtual stock exchange.

The store is deliberately in-memory for local development and deterministic tests.
The service boundary keeps persistence replaceable with PostgreSQL transactions.
"""

from __future__ import annotations

import asyncio
import secrets
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, ConfigDict, Field

from .scenarios import SCENARIOS, STOCKS
from .market import MarketEngine, MarketPort, WebSocketHub

STARTING_CASH = 25_000.0
PRICE_FLOOR = 10.0
MAX_SHARES = 40
MAX_CONCENTRATION = 0.35


class Role(str, Enum):
    ADMIN = "ADMIN"
    PARTICIPANT = "PARTICIPANT"


class UserStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"


class OrderAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"


@dataclass
class User:
    id: str
    full_name: str
    email: str
    registration_no: str
    role: Role = Role.PARTICIPANT
    status: UserStatus = UserStatus.PENDING
    cash: float = STARTING_CASH
    collateral: float = 0.0
    credited: float = STARTING_CASH
    positions: dict[tuple[str, str], dict[str, float]] = field(default_factory=dict)


@dataclass
class Stock:
    symbol: str
    company_name: str
    sector: str
    anchor_price: float
    current_price: float
    pe_ratio: float


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=3, max_length=255)
    registration_no: str = Field(min_length=2, max_length=50)


class OrderRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    symbol: str = Field(min_length=1, max_length=12)
    action: OrderAction
    quantity: int = Field(gt=0, le=MAX_SHARES)


class ScenarioRequest(BaseModel):
    scenario_id: str


class MarketStore:
    def __init__(self) -> None:
        self.lock = RLock()
        self.users: dict[str, User] = {}
        self.tokens: dict[str, str] = {}
        self.stocks = {s[0]: Stock(s[0], s[1], s[2], s[3], s[3], s[4]) for s in STOCKS}
        self.market_open = True
        self.ticks_enabled = True
        self.leaderboard_frozen = False
        self.frozen_leaderboard: list[dict[str, Any]] = []
        self.active_scenario = "BASE"
        self._seed_admin()

    def _seed_admin(self) -> None:
        admin = User("admin", "GENESIS Admin", "admin@genesis.local", "ADMIN", Role.ADMIN, UserStatus.ACTIVE)
        self.users[admin.id] = admin
        self.tokens["admin-token"] = admin.id

    def authenticate(self, token: str | None, role: Role | None = None) -> User:
        user_id = self.tokens.get(token or "")
        user = self.users.get(user_id or "")
        if not user or (role and user.role != role) or user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        return user

    def portfolio(self, user: User) -> dict[str, Any]:
        long_value = short_liability = 0.0
        holdings = []
        for (symbol, side), position in user.positions.items():
            price = self.stocks[symbol].current_price
            value = position["quantity"] * price
            if side == "LONG":
                long_value += value
            else:
                short_liability += value
            holdings.append({"symbol": symbol, "side": side, "quantity": int(position["quantity"]), "avg_entry_price": round(position["avg_entry_price"], 2), "market_value": round(value, 2)})
        net_worth = user.cash + long_value + user.collateral - short_liability
        return {"cash": round(user.cash, 2), "collateral_locked": round(user.collateral, 2), "long_value": round(long_value, 2), "short_liability": round(short_liability, 2), "net_worth": round(net_worth, 2), "pnl": round(net_worth - user.credited, 2), "holdings": holdings}

    def execute_order(self, user: User, request: OrderRequest) -> dict[str, Any]:
        with self.lock:
            if not self.market_open:
                raise HTTPException(status_code=423, detail="Market is paused")
            symbol = request.symbol.upper()
            stock = self.stocks.get(symbol)
            if not stock:
                raise HTTPException(status_code=404, detail="Unknown stock symbol")
            qty = request.quantity
            price = stock.current_price
            action = request.action
            key = (symbol, "LONG" if action in (OrderAction.BUY, OrderAction.SELL) else "SHORT")
            position = user.positions.get(key, {"quantity": 0.0, "avg_entry_price": price})
            if action == OrderAction.BUY:
                if user.cash < qty * price:
                    raise HTTPException(status_code=400, detail="Insufficient cash")
                if position["quantity"] + qty > MAX_SHARES:
                    raise HTTPException(status_code=400, detail="Position exceeds 40-share cap")
                current_net_worth = self.portfolio(user)["net_worth"]
                post_trade_value = (position["quantity"] + qty) * price
                if post_trade_value > current_net_worth * MAX_CONCENTRATION:
                    raise HTTPException(status_code=400, detail="Order exceeds 35% single-stock concentration cap")
                user.cash -= qty * price
                position["avg_entry_price"] = ((position["quantity"] * position["avg_entry_price"]) + qty * price) / (position["quantity"] + qty)
                position["quantity"] += qty
            elif action == OrderAction.SELL:
                if position["quantity"] < qty:
                    raise HTTPException(status_code=400, detail="Insufficient long shares")
                user.cash += qty * price
                position["quantity"] -= qty
            elif action == OrderAction.SHORT:
                required = qty * price
                if user.cash - user.collateral < required:
                    raise HTTPException(status_code=400, detail="Insufficient free cash for short collateral")
                if position["quantity"] + qty > MAX_SHARES:
                    raise HTTPException(status_code=400, detail="Position exceeds 40-share cap")
                user.collateral += required
                position["avg_entry_price"] = ((position["quantity"] * position["avg_entry_price"]) + qty * price) / (position["quantity"] + qty)
                position["quantity"] += qty
            else:
                if position["quantity"] < qty:
                    raise HTTPException(status_code=400, detail="Insufficient short shares")
                entry = position["avg_entry_price"]
                user.collateral -= qty * entry
                user.cash += qty * entry + qty * (entry - price)
                position["quantity"] -= qty
            if position["quantity"]:
                user.positions[key] = position
            else:
                user.positions.pop(key, None)
            return {"symbol": symbol, "action": action, "quantity": qty, "execution_price": round(price, 2), "portfolio": self.portfolio(user)}

    def trigger_scenario(self, scenario_id: str) -> dict[str, Any]:
        with self.lock:
            scenario = SCENARIOS.get(scenario_id)
            if not scenario:
                raise HTTPException(status_code=404, detail="Unknown scenario")
            for symbol, delta in scenario[2].items():
                stock = self.stocks[symbol]
                stock.current_price = max(PRICE_FLOOR, round(stock.current_price * (1 + delta), 2))
                stock.anchor_price = stock.current_price
            self.active_scenario = scenario_id
            return self.market_snapshot()

    def market_snapshot(self) -> dict[str, Any]:
        return {"active_scenario": self.active_scenario, "market_open": self.market_open, "ticks_enabled": self.ticks_enabled, "stocks": [{"symbol": s.symbol, "name": s.company_name, "sector": s.sector, "price": round(s.current_price, 2), "anchor_price": round(s.anchor_price, 2)} for s in self.stocks.values()]}

    def price_snapshot(self) -> dict[str, tuple[float, float]]:
        return {symbol: (stock.current_price, stock.anchor_price) for symbol, stock in self.stocks.items()}

    def set_price(self, symbol: str, price: float) -> None:
        stock = self.stocks[symbol]
        stock.current_price = max(PRICE_FLOOR, round(price, 2))

    def leaderboard(self) -> list[dict[str, Any]]:
        rows = [{"user_id": u.id, "name": u.full_name, "net_worth": self.portfolio(u)["net_worth"]} for u in self.users.values() if u.role == Role.PARTICIPANT and u.status == UserStatus.ACTIVE]
        return sorted(rows, key=lambda row: row["net_worth"], reverse=True)


store = MarketStore()
market_port: MarketPort = store
market_engine = MarketEngine(market_port)
market_hub = WebSocketHub()


async def publish_ticks(ticks: list[dict[str, Any]]) -> None:
    await market_hub.broadcast({"event": "PRICE_TICK", "data": ticks})


@asynccontextmanager
async def lifespan(_: FastAPI):
    market_engine.enabled = store.ticks_enabled
    market_engine.start(publish_ticks)
    try:
        yield
    finally:
        await market_engine.stop()


app = FastAPI(title="GENESIS 2026 API", version="1.0.0", lifespan=lifespan)


def current_user(authorization: Annotated[str | None, Header()] = None) -> User:
    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    return store.authenticate(token)


def admin_user(authorization: Annotated[str | None, Header()] = None) -> User:
    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    return store.authenticate(token, Role.ADMIN)


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "GENESIS backend running", "version": app.version}


@app.get("/api/v1/market")
def market() -> dict[str, Any]:
    return store.market_snapshot()


@app.post("/api/v1/auth/register", status_code=201)
def register(request: RegisterRequest) -> dict[str, Any]:
    if any(u.email == request.email or u.registration_no == request.registration_no for u in store.users.values()):
        raise HTTPException(status_code=409, detail="Email or registration number already registered")
    user = User(secrets.token_hex(8), request.full_name, request.email, request.registration_no)
    store.users[user.id] = user
    return {"id": user.id, "status": user.status, "message": "Registration submitted for admin approval"}


@app.post("/api/v1/auth/login")
def login(email: str, registration_no: str) -> dict[str, Any]:
    user = next((u for u in store.users.values() if u.email == email and u.registration_no == registration_no), None)
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Account is pending approval or credentials are invalid")
    token = secrets.token_urlsafe(24)
    store.tokens[token] = user.id
    return {"access_token": token, "token_type": "bearer", "role": user.role}


@app.patch("/api/v1/admin/users/{user_id}/approve")
def approve_user(user_id: str, _: User = Depends(admin_user)) -> dict[str, Any]:
    user = store.users.get(user_id)
    if not user or user.role != Role.PARTICIPANT:
        raise HTTPException(status_code=404, detail="Participant not found")
    user.status = UserStatus.ACTIVE
    return {"id": user.id, "status": user.status}


@app.post("/api/v1/trade/order")
def order(request: OrderRequest, user: User = Depends(current_user)) -> dict[str, Any]:
    return store.execute_order(user, request)


@app.get("/api/v1/portfolio/me")
def portfolio(user: User = Depends(current_user)) -> dict[str, Any]:
    return store.portfolio(user)


@app.get("/api/v1/leaderboard")
def leaderboard(user: User = Depends(current_user)) -> dict[str, Any]:
    rows = store.leaderboard()
    if store.leaderboard_frozen and user.role == Role.PARTICIPANT:
        rows = store.frozen_leaderboard
    return {"frozen": store.leaderboard_frozen, "entries": rows}


@app.post("/api/v1/admin/scenario/trigger")
def trigger_scenario(request: ScenarioRequest, _: User = Depends(admin_user)) -> dict[str, Any]:
    return store.trigger_scenario(request.scenario_id)


@app.patch("/api/v1/admin/market/pause")
def toggle_market(_: User = Depends(admin_user)) -> dict[str, bool]:
    store.market_open = not store.market_open
    return {"market_open": store.market_open}


@app.patch("/api/v1/admin/ticks/toggle")
def toggle_ticks(_: User = Depends(admin_user)) -> dict[str, bool]:
    store.ticks_enabled = not store.ticks_enabled
    market_engine.enabled = store.ticks_enabled
    return {"ticks_enabled": store.ticks_enabled}


@app.post("/api/v1/admin/leaderboard/freeze")
def freeze_leaderboard(_: User = Depends(admin_user)) -> dict[str, bool]:
    store.leaderboard_frozen = not store.leaderboard_frozen
    if store.leaderboard_frozen:
        store.frozen_leaderboard = store.leaderboard()
    return {"leaderboard_frozen": store.leaderboard_frozen}


async def market_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    client = await market_hub.add(websocket)
    heartbeat_task = asyncio.create_task(market_hub.heartbeat_loop())
    try:
        await market_hub.send(client, {"event": "MARKET_SNAPSHOT", "data": store.market_snapshot()})
        while True:
            message = await websocket.receive_json()
            market_hub.mark_seen(websocket)
            if message.get("type") in {"PING", "ping"}:
                await market_hub.send(client, {"event": "PONG"})
            elif message.get("type") in {"PONG", "pong"}:
                continue
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        heartbeat_task.cancel()
        await asyncio.gather(heartbeat_task, return_exceptions=True)
        await market_hub.remove(websocket)


app.websocket("/market/ticks")(market_stream)
app.websocket("/ws/market")(market_stream)
