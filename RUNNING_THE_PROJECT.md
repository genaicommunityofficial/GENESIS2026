# Running GENESIS 2026

This guide explains how to start the database container, FastAPI backend container, and Vite frontend server for local development.

## What runs where

- **PostgreSQL container (`db`)** stores accounts, wallets, trades, and market state.
- **FastAPI container (`backend`)** serves the API on port `8000` inside Docker. The development Compose override maps it to `127.0.0.1:8000` so Vite can proxy API and WebSocket requests.
- **Vite frontend server** runs on your Mac at `http://localhost:5173` and serves the React app.

## One-time setup

Start Docker Desktop and wait for it to report that Docker is running. In Terminal:

```bash
cd /Users/rishabjain/developer/genesis2026
cp .env.example .env
```

Edit `.env`: set a private `ADMIN_PASSWORD` and a long random `JWT_SECRET`. Keep `POSTGRES_PASSWORD` the same after the database is first created; changing the value in `.env` does not update an existing database volume.

Create the database schema, seed the 30 companies, and create the admin account:

```bash
docker compose run --rm backend python -m app.seed
```

Start the database and backend containers with the local development port mapping:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db backend
```

In a second Terminal window, install frontend dependencies once and start Vite:

```bash
cd /Users/rishabjain/developer/genesis2026/frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. Leave the Vite terminal running while you use the app.

## Starting it again later

Start Docker Desktop, then start the existing database and backend containers:

```bash
cd /Users/rishabjain/developer/genesis2026
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db backend
```

In another terminal:

```bash
cd /Users/rishabjain/developer/genesis2026/frontend
npm run dev
```

Do not run the seed command again during normal startup. The database volume preserves participant accounts, trades, and event progress.

## Check that the servers are running

Check container status:

```bash
cd /Users/rishabjain/developer/genesis2026
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

Check the API health response:

```bash
curl http://localhost:8000/api/health
```

Expected response includes `"ok":true`. `"market_open":false` is normal on startup; an admin opens the market from the Control room.

To inspect backend or database output:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs --tail=100 backend
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs --tail=100 db
```

## Admin and participant flow

1. Sign in with the `ADMIN_EMAIL` and `ADMIN_PASSWORD` values from `.env`.
2. In **Control room**, approve participant registrations.
3. Open the market before participants place orders.
4. Trigger eras in order. Each era can run only once per database.

Participants register from the login page. Their account remains pending until an admin approves it.

## Stop the local app

Stop the frontend server with **Ctrl+C** in its terminal. Then stop the containers while preserving database data:

```bash
cd /Users/rishabjain/developer/genesis2026
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

## Rebuild the backend container

After changing backend code, rebuild and restart the backend:

```bash
cd /Users/rishabjain/developer/genesis2026
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build backend
```

## Reset for a new event

This erases all database records and event progress. Run only when you want a clean event:

```bash
cd /Users/rishabjain/developer/genesis2026
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
docker compose run --rm backend python -m app.seed
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db backend
```

The frontend can stay running during a reset; refresh the browser after the backend is healthy.

## Production container

Production uses Nginx to serve the built frontend and proxy API/WebSocket traffic over HTTPS/WSS on port `443`. Before starting production Compose, configure `.env` and provide `nginx/certs/fullchain.pem` and `nginx/certs/privkey.pem`. Seed the database once, then run:

```bash
docker compose up -d --build
```

Production Compose keeps the backend port private. Use the development override only for local Vite development.
