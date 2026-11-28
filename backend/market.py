"""In-memory market engine and WebSocket hub primitives for M5/M6."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from fastapi import WebSocket


class MarketPort(Protocol):
    """Persistence-independent port used by the market engine."""

    def price_snapshot(self) -> dict[str, tuple[float, float]]: ...

    def set_price(self, symbol: str, price: float) -> None: ...


class MarketEngine:
    """Generate bounded, mean-reverting in-memory price ticks."""

    def __init__(self, market: MarketPort, *, interval_seconds: float = 5.0, seed: int | None = None) -> None:
        self.market = market
        self.interval_seconds = interval_seconds
        self.random = random.Random(seed)
        self.enabled = True
        self._task: asyncio.Task[None] | None = None

    def tick(self) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        changes: list[dict[str, Any]] = []
        for symbol, (current, anchor) in self.market.price_snapshot().items():
            volatility = 0.003 if symbol in {"TMND", "VRID", "PAYB", "OMNA", "BCHIP"} else 0.001
            distance = (anchor - current) / anchor
            change_pct = self.random.gauss(0.0, volatility) + (0.15 * distance)
            next_price = max(10.0, round(current * (1.0 + change_pct), 2))
            self.market.set_price(symbol, next_price)
            changes.append({"symbol": symbol, "price": next_price, "change_pct": round((next_price / current - 1.0) * 100, 4)})
        return changes

    async def run(self, publish: Any) -> None:
        while True:
            try:
                if self.enabled:
                    ticks = self.tick()
                    if ticks:
                        await publish(ticks)
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                raise
            except Exception:
                # A transient tick failure must not kill the application loop.
                await asyncio.sleep(self.interval_seconds)

    def start(self, publish: Any) -> asyncio.Task[None]:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run(publish))
        return self._task

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        self._task = None


@dataclass
class HubClient:
    websocket: WebSocket
    last_seen: float = field(default_factory=time.monotonic)
    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class WebSocketHub:
    """Track market clients, send heartbeats, and evict stale connections."""

    def __init__(self, *, heartbeat_seconds: float = 15.0, eviction_seconds: float = 45.0) -> None:
        self.heartbeat_seconds = heartbeat_seconds
        self.eviction_seconds = eviction_seconds
        self.clients: dict[int, HubClient] = {}

    async def add(self, websocket: WebSocket) -> HubClient:
        client = HubClient(websocket)
        self.clients[id(websocket)] = client
        return client

    async def remove(self, websocket: WebSocket) -> None:
        self.clients.pop(id(websocket), None)

    def mark_seen(self, websocket: WebSocket) -> None:
        client = self.clients.get(id(websocket))
        if client:
            client.last_seen = time.monotonic()

    async def send(self, client: HubClient, payload: dict[str, Any]) -> None:
        async with client.send_lock:
            await client.websocket.send_json(payload)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        results = await asyncio.gather(*(self.send(client, payload) for client in tuple(self.clients.values())), return_exceptions=True)
        for client, result in zip(tuple(self.clients.values()), results):
            if isinstance(result, Exception):
                await self.remove(client.websocket)

    async def heartbeat_once(self) -> list[WebSocket]:
        now = time.monotonic()
        evicted: list[WebSocket] = []
        for client in tuple(self.clients.values()):
            if now - client.last_seen > self.eviction_seconds:
                evicted.append(client.websocket)
                await self.remove(client.websocket)
                continue
            try:
                await self.send(client, {"event": "PING", "ts": datetime.now(timezone.utc).isoformat()})
            except Exception:
                evicted.append(client.websocket)
                await self.remove(client.websocket)
        return evicted

    async def heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(self.heartbeat_seconds)
            await self.heartbeat_once()

