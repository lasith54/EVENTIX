#!/bin/bash
# scripts/load-test.sh
# Simple load testing script

set -e

echo "🔄 EVENTIX Load Test"
echo "=================="

# Configuration
BASE_URL="http://localhost"
CONCURRENT_REQUESTS=10
TOTAL_REQUESTS=100

echo "Configuration:"
echo "  Base URL: $BASE_URL"
echo "  Concurrent Requests: $CONCURRENT_REQUESTS"
echo "  Total Requests: $TOTAL_REQUESTS"
echo ""

# Test health endpoint
echo "Testing health endpoint..."
ab -n $TOTAL_REQUESTS -c $CONCURRENT_REQUESTS "$BASE_URL/health"

echo ""

# Test events endpoint
echo "Testing events endpoint..."
ab -n $TOTAL_REQUESTS -c $CONCURRENT_REQUESTS "$BASE_URL/api/v1/events/"

echo ""
echo "Load test complete!"

---

# Makefile
# EVENTIX Project Makefile

.PHONY: help install deploy start stop restart logs health test clean backup

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install and setup the project
	@chmod +x scripts/*.sh
	@echo "✅ Project setup complete!"

deploy: ## Deploy the entire EVENTIX system
	@./scripts/deploy.sh

start: ## Start all services
	@./scripts/manage.sh start

stop: ## Stop all services
	@./scripts/manage.sh stop

restart: ## Restart all services
	@./scripts/manage.sh restart

logs: ## View logs for all services
	@./scripts/manage.sh logs

health: ## Check system health
	@./scripts/health-check.sh

test: ## Run load tests
	@./scripts/load-test.sh

backup: ## Create database backup
	@./scripts/backup.sh

clean: ## Clean up containers and volumes
	@docker-compose down -v --remove-orphans
	@docker system prune -f
	@echo "✅ Cleanup complete!"

scale: ## Scale services for