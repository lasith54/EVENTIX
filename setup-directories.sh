#!/bin/bash
# setup-directories.sh
# Script to create all required directories and files for EVENTIX

echo "🏗️  Setting up EVENTIX directory structure..."

# Create main directories
mkdir -p monitoring/grafana/datasources
mkdir -p monitoring/grafana/dashboards
mkdir -p scripts
mkdir -p shared
mkdir -p services/user-service/routes
mkdir -p services/user-service/services
mkdir -p services/user-service/tests
mkdir -p services/event-service/routes
mkdir -p services/event-service/services
mkdir -p services/event-service/tests
mkdir -p services/booking-service/routes
mkdir -p services/booking-service/services
mkdir -p services/booking-service/tests
mkdir -p services/payment-service/routes
mkdir -p services/payment-service/services
mkdir -p services/payment-service/tests
mkdir -p services/api-gateway/middleware
mkdir -p services/api-gateway/routes
mkdir -p services/api-gateway/tests
mkdir -p tests/integration
mkdir -p tests/load
mkdir -p tests/fixtures
mkdir -p deployment/kubernetes
mkdir -p deployment/terraform
mkdir -p deployment/ansible
mkdir -p config
mkdir -p data/backups
mkdir -p data/logs
mkdir -p data/uploads
mkdir -p ssl
mkdir -p docs

echo "✅ Directories created successfully!"

# Create essential empty files
echo "📄 Creating essential files..."

# Root level files
touch .env.example
touch .gitignore
touch .dockerignore
touch requirements.txt
touch pytest.ini
touch mypy.ini
touch black.toml
touch isort.cfg
touch CONTRIBUTING.md
touch LICENSE
touch CHANGELOG.md

# Shared module files
touch shared/__init__.py
touch shared/auth.py
touch shared/cache.py
touch shared/logging_config.py
touch shared/metrics.py

# Service __init__.py files
find services -type d -name "routes" -o -name "services" -o -name "tests" | xargs -I {} touch {}/__init__.py
touch services/user-service/__init__.py
touch services/event-service/__init__.py
touch services/booking-service/__init__.py
touch services/payment-service/__init__.py
touch services/api-gateway/__init__.py

# Test module files
touch tests/__init__.py
touch tests/integration/__init__.py
touch tests/load/__init__.py
touch tests/fixtures/__init__.py

# Config files
touch config/development.env
touch config/production.env
touch config/testing.env

echo "✅ Essential files created!"

# Make the script executable
chmod +x setup-directories.sh

echo "🎉 Setup complete! You can now create the monitoring files."
echo ""
echo "Next steps:"
echo "1. Run: ./setup-directories.sh"
echo "2. Create the configuration files using the provided artifacts"
echo "3. Deploy with: make deploy"