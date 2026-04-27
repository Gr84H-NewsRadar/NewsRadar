#!/bin/bash
set -e

echo "Deploying NewsRadar..."

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down

# Build and start containers
echo "Starting containers..."
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to be ready..."
sleep 10

# Check health
echo "Checking API health..."
curl -f http://localhost:8000/api/v1/health || exit 1

echo "Deployment complete!"
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo "MailHog: http://localhost:8025"
