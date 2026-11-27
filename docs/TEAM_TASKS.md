# Who builds what (search for TODO in the code)

| Owner | Files | TODOs |
|---|---|---|
| Backend: trading | `services/trading.py`, `routers/trade.py`, `tests/test_trading.py` | BUY/SELL/SHORT/COVER, caps, forced cover, portfolio endpoint, tests first |
| Backend: admin/auth | `routers/auth.py`, `routers/admin.py`, `services/scenarios.py` | register, approvals + wallet creation, top-ups, audit, in-flight trade lock, DB writes on era |
| Realtime/infra | `services/ws_manager.py`, `tick_engine.py`, `leaderboard.py`, `nginx/`, `docker-compose.yml` | WS auth, send timeouts, rankings SQL, freeze snapshot, TLS, load test |
| Frontend: participant | `pages/Trading,Portfolio,Leaderboard`, `components/*` | filters, charts, order modal (real company_id), banners |
| Frontend: admin | `pages/AdminDashboard.jsx` | 2-step Yapoo, queues, audit viewer, live ranks |

## Open decisions (settle in week 1)
- 35% cap: of net worth or of starting capital? Checked at order time only?
- Does a forced cover bypass the market-paused flag?
- Sigma per stock: derive from P/E or a flat value?
