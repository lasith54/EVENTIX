#!/bin/bash
# scripts/health-check.sh
# Comprehensive health check script

set -e

echo "🏥 EVENTIX Health Check"
echo "======================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local service_name=$1
    local url=$2
    local timeout=${3:-10}
    
    echo -n "Checking $service_name... "
    
    if curl -f -s --max-time $timeout "$url" > /dev/null; then
        echo -e "${GREEN}✓ Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        return 1
    fi
}

check_database() {
    echo -n "Checking Database... "
    
    if docker exec eventix-db pg_isready -U eventix_user -d eventix > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        return 1
    fi
}

check_redis() {
    echo -n "Checking Redis... "
    
    if docker exec eventix-redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        return 1
    fi
}

# Main health checks
echo "Infrastructure Services:"
check_database
check_redis
echo ""

echo "Application Services:"
check_service "API Gateway" "http://localhost/health"
check_service "User Service" "http://localhost:8000/health"
check_service "Event Service" "http://localhost:8001/health"
check_service "Booking Service" "http://localhost:8002/health"
check_service "Payment Service" "http://localhost:8003/health"
echo ""

echo "Monitoring Services:"
check_service "Grafana" "http://localhost:3000/api/health"
check_service "Prometheus" "http://localhost:9090/-/healthy"
echo ""

echo "Load Balancer:"
check_service "Nginx" "http://localhost/nginx-health"
echo ""

# API functionality test
echo "API Functionality Test:"
echo -n "Testing API endpoints... "
if curl -f -s "http://localhost/api/v1/events/" > /dev/null; then
    echo -e "${GREEN}✓ API Working${NC}"
else
    echo -e "${RED}✗ API Not Working${NC}"
fi

echo ""
echo "Health check complete!"

---