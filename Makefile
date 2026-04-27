.PHONY: help build run test deploy clean logs

help:
	@echo "NewsRadar - Available commands:"
	@echo "  make build   - Build Docker images"
	@echo "  make run     - Run application with Docker Compose"
	@echo "  make test    - Run tests"
	@echo "  make deploy  - Deploy application"
	@echo "  make clean   - Clean up containers and volumes"
	@echo "  make logs    - Show application logs"
	@echo "  make shell   - Open shell in API container"

build:
	docker-compose build

run:
	docker-compose up -d
	@echo "Application started!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "MailHog: http://localhost:8025"

test:
	cd newsradar_api && pytest tests/ -v --cov=app

deploy:
	bash scripts/deploy.sh

clean:
	docker-compose down -v
	rm -f newsradar_api/*.db

logs:
	docker-compose logs -f api

shell:
	docker-compose exec api /bin/bash

stop:
	docker-compose down

restart:
	docker-compose restart

ps:
	docker-compose ps
