# GENESIS 2026: Virtual Stock Exchange

GENESIS is a virtual stock market simulation with a React frontend, FastAPI backend, and PostgreSQL database. This guide covers the local development flow: first-time setup, starting the app again, running the event as an admin, stopping it, and resetting the event.

For a focused server/container startup guide, see [RUNNING_THE_PROJECT.md](RUNNING_THE_PROJECT.md).

## Requirements

- Docker Desktop, running
- Node.js 18 or newer

## First-time setup

Open a terminal in the project folder:

```bash
cd /Users/rishabjain/developer/genesis2026
cp .env.example .env
```

Edit `.env` and set a private `ADMIN_PASSWORD` and a long random `JWT_SECRET`. Keep `POSTGRES_PASSWORD` unchanged after the database is initialized; changing it later does not change the password stored in the existing database volume.

Initialize the database schema, seed the 30 companies and create the admin account:

```bash
docker compose run --rm backend python -m app.seed
```

Start the database and backend with the local development port mapping:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db backend
```

In a second terminal, start the frontend:

```bash
cd /Users/rishabjain/developer/genesis2026/frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Keep the frontend terminal open while using the app. The frontend proxies API and WebSocket requests to FastAPI at `127.0.0.1:8000`.

## Start the project again

Start Docker Desktop first. In a terminal:

```bash
cd /Users/rishabjain/developer/genesis2026
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db backend
```

In another terminal:

```bash
cd /Users/rishabjain/developer/genesis2026/frontend
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173). Do not run the seed command on every startup. PostgreSQL keeps your accounts, trades, and event state in its Docker volume.

If you changed backend code and need to rebuild it, use:

```bash
cd /Users/rishabjain/developer/genesis2026
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build db backend
```

## Admin and event flow

1. Sign in with `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `.env`.
2. In **Control room**, approve participant registrations. New participant accounts remain pending until approved.
3. Open trading. The market starts paused.
4. Trigger eras in order, from Era 1 through Era 10. Each era can only be triggered once per database and cannot be replayed.
5. Use the admin controls to pause trading, toggle price ticks, review top-up requests, and freeze or reveal the leaderboard.

Participants register from the login page, wait for approval, then sign in to trade. Their portfolio shows cash, collateral, open positions, P&L, and recent transactions.

## Stop the project

Stop the Vite frontend with **Ctrl+C** in its terminal. Then stop the backend and database containers:

```bash
cd /Users/rishabjain/developer/genesis2026
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

This preserves the database volume. Start again using the **Start the project again** steps above.

## Reset the event and erase database data

This permanently deletes all registered participants, wallets, trades, top-up requests, and era history. Run it only when you want a new event from the beginning:

```bash
cd /Users/rishabjain/developer/genesis2026
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
docker compose run --rm backend python -m app.seed
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db backend
```

The seed command recreates the company catalog and admin account using the current `.env`. Start the frontend again with `npm run dev`.

## Production deployment

Production Compose builds the frontend into the Nginx image and serves HTTPS/WSS on port 443. Configure `.env`, place a valid certificate and private key at `nginx/certs/fullchain.pem` and `nginx/certs/privkey.pem`, then run:

```bash
docker compose up -d --build
```

The production setup does not publish the FastAPI port. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the service layout.

## Included functionality

- Participant registration, admin approval, and JWT login
- Live prices for 30 fictional companies and 10 chronological eras
- Instant buy, sell, short, and cover orders
- 35% single-company concentration limit, 40-share limit, price floor, short collateral, and forced covers
- Participant portfolio, transaction history, leaderboard, and leaderboard freeze
- Admin market controls, top-up approval, and audit log

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest -q
```
