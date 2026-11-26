"""WebSocket hub. Message types: PRICE_UPDATE, ERA_TRIGGERED, RANK_UPDATE, MARKET_STATUS, PONG."""
import asyncio, json
from fastapi import WebSocket

class WSManager:
    def __init__(self): self.clients: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept(); self.clients.add(ws)

    def disconnect(self, ws: WebSocket): self.clients.discard(ws)

    async def broadcast(self, msg: dict):
        data = json.dumps(msg)
        clients = list(self.clients)
        if not clients: return
        results = await asyncio.gather(*(asyncio.wait_for(ws.send_text(data), timeout=2) for ws in clients), return_exceptions=True)
        for ws, result in zip(clients, results):
            if isinstance(result, BaseException): self.disconnect(ws)

ws_manager = WSManager()
