up:
	docker compose up -d --build
down:
	docker compose down
logs:
	docker compose logs -f backend
test:
	cd backend && pytest -q
seed:
	docker compose exec backend python -m app.seed
