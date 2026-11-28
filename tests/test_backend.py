import pytest
from fastapi import HTTPException

import asyncio

from backend.main import OrderAction, OrderRequest, RegisterRequest, ScenarioRequest, UserStatus, app, health_check, login, order, portfolio, register, store, toggle_market, trigger_scenario
from backend.market import MarketEngine, WebSocketHub
from backend.scenarios import STOCKS


def setup_function() -> None:
    store.market_open = True
    store.ticks_enabled = True
    store.leaderboard_frozen = False
    store.frozen_leaderboard = []
    store.active_scenario = "BASE"
    for stock in store.stocks.values():
        stock.current_price = stock.anchor_price = next(row[3] for row in STOCKS if row[0] == stock.symbol)


def register_and_approve(name: str) -> object:
    registration = f"22BCE{len(store.users) + 1000:04d}"
    result = register(RegisterRequest(full_name=name, email=f"{name.lower().replace(' ', '.')}@vit.ac.in", registration_no=registration))
    user = store.users[result["id"]]
    user.status = UserStatus.ACTIVE
    login_result = login(email=user.email, registration_no=user.registration_no)
    return user, login_result["access_token"]


def test_registration_requires_approval_and_health() -> None:
    assert health_check()["status"] == "GENESIS backend running"
    result = register(RegisterRequest(full_name="Pending User", email="pending@vit.ac.in", registration_no="22BCE0002"))
    assert result["status"] == UserStatus.PENDING
    with pytest.raises(HTTPException) as error:
        login(email="pending@vit.ac.in", registration_no="22BCE0002")
    assert error.value.status_code == 403


def test_buy_sell_and_portfolio() -> None:
    user, _ = register_and_approve("Rachit Singh")
    buy = order(OrderRequest(symbol="TMND", action=OrderAction.BUY, quantity=10), user)
    assert buy["execution_price"] == 180.0
    assert portfolio(user)["holdings"][0]["quantity"] == 10
    assert portfolio(user)["net_worth"] == 25000.0
    order(OrderRequest(symbol="TMND", action=OrderAction.SELL, quantity=10), user)
    assert portfolio(user)["holdings"] == []


def test_short_collateral_and_cover_profit() -> None:
    user, _ = register_and_approve("Short Seller")
    order(OrderRequest(symbol="TMND", action=OrderAction.SHORT, quantity=10), user)
    trigger_scenario(ScenarioRequest(scenario_id="ERA_1_DOT_COM"), store.users["admin"])
    covered = order(OrderRequest(symbol="TMND", action=OrderAction.COVER, quantity=10), user)
    assert covered["portfolio"]["collateral_locked"] == 0.0
    assert covered["portfolio"]["pnl"] > 0


def test_guardrails_and_admin_controls() -> None:
    user, _ = register_and_approve("Guardrail User")
    with pytest.raises(Exception):
        order(OrderRequest(symbol="TMND", action=OrderAction.BUY, quantity=41), user)
    assert toggle_market(store.users["admin"])["market_open"] is False
    with pytest.raises(HTTPException) as error:
        order(OrderRequest(symbol="TMND", action=OrderAction.BUY, quantity=1), user)
    assert error.value.status_code == 423


def test_m5_market_engine_respects_floor_and_emits_ticks() -> None:
    engine = MarketEngine(store, seed=7)
    ticks = engine.tick()
    assert len(ticks) == 30
    assert all(tick["price"] >= 10.0 for tick in ticks)
    assert {tick["symbol"] for tick in ticks} == set(store.stocks)


def test_m6_hub_evicts_stale_clients() -> None:
    class FakeWebSocket:
        async def send_json(self, payload: dict) -> None:
            return None

    async def scenario() -> None:
        hub = WebSocketHub(heartbeat_seconds=1, eviction_seconds=0)
        websocket = FakeWebSocket()
        await hub.add(websocket)
        evicted = await hub.heartbeat_once()
        assert evicted == [websocket]
        assert not hub.clients

    asyncio.run(scenario())
    assert "/market/ticks" in {route.path for route in app.routes}
