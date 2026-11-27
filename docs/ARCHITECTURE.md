# GENESIS 2026: Architecture

```
 Browser (React SPA)
   │  https://host/        → static files (Nginx)
   │  https://host/api/*   → FastAPI REST
   │  wss://host/ws        → FastAPI WebSocket      (all on port 443)
   ▼
 Nginx :443 ──► FastAPI (1 worker) ──► PostgreSQL (private network, never exposed)
                 │  RAM: prices, anchors, flags, leaderboard cache
                 ├─ tick_engine.supervisor()   (jitter every 5–8s, RAM only)
                 └─ leaderboard_loop()         (batch rank every ~3s)
```

## Design rules
1. **Prices live in RAM.** Trades read `app_state.prices`. Postgres is written only on trades and eras.
2. **One uvicorn worker.** RAM state and the WS hub are per-process. Scaling out needs Redis (not planned).
3. **Dealer model.** Every valid order fills instantly. Rejections: paused market (423), cash, 35% cap, 40-share cap.
4. **Wallet row lock.** `SELECT ... FOR UPDATE` on the user's wallet serialises that user's orders.
5. **Eras are idempotent.** `scenario_executions.scenario_id` is UNIQUE, so a double-click returns 409.
6. **Leaderboard.** Participants read the cache, which stops updating when frozen. Admins read `admin_live`.
7. **Only port 443 is public.** The DB sits on the internal Docker network.

## WebSocket messages (server → client)
| type | payload |
|---|---|
| PRICE_UPDATE | `{prices: {SYM: price}}` |
| ERA_TRIGGERED | `{scenario, prices}` |
| RANK_UPDATE | `{ranks: [...]}` |
| MARKET_STATUS | `{open: bool}` |
| PONG | reply to client `{type:"PING"}` every 15s |

## Request flow: placing an order
`POST /trade/order` → JWT role check → market-open check → BEGIN → lock wallet → price from RAM → rule checks → update wallet/holdings → insert transaction → COMMIT.

## Spec fixes applied vs PRD
- Jitter formula normalises the anchor gap: `(P − Anchor)/Anchor`.
- Tick interval is 5–8s (PRD header said 3–5s).
- Added `password_hash`, `transactions`, `topup_requests` (UNIQUE user), `scenario_executions`, `audit_log`, `leaderboard_snapshot`.
