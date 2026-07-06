.PHONY: start stop reset test demo docker-up docker-down docker-reset lint typecheck build

start:
	bash scripts/start-local.sh

stop:
	bash scripts/stop-local.sh

reset:
	bash scripts/reset-local-data.sh

test:
	cd backend && .venv/bin/python -m pytest -q
	cd frontend && npm run lint && npx tsc --noEmit

lint:
	cd frontend && npm run lint

typecheck:
	cd frontend && npx tsc --noEmit

build:
	cd frontend && npm run build

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-reset:
	docker compose down -v
	@echo "Named volume removed. Next 'make docker-up' starts fresh."
