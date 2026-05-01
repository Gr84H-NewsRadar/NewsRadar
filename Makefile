DC := $(shell docker compose version > /dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

.PHONY: help build run test deploy clean logs shell stop restart ps

help:
	@echo "NewsRadar - Available commands:"
	@echo "  make build    - Build Docker images"
	@echo "  make run      - Run application with Docker Compose"
	@echo "  make test     - Run tests inside container"
	@echo "  make deploy   - Deploy application (build + run + healthcheck)"
	@echo "  make clean    - Clean up containers and volumes"
	@echo "  make logs     - Show application logs"
	@echo "  make shell    - Open shell in API container"
	@echo "  make stop     - Stop containers"
	@echo "  make restart  - Restart containers"
	@echo "  make ps       - Show container status"

build:
	bash scripts/build.sh

run:
	bash scripts/run.sh

test:
	bash scripts/test.sh

deploy:
	bash scripts/deploy.sh

clean:
	$(DC) down -v
	rm -f newsradar_api/*.db

logs:
	$(DC) logs -f api

shell:
	$(DC) exec api /bin/bash

stop:
	$(DC) down

restart:
	$(DC) restart

ps:
	$(DC) ps