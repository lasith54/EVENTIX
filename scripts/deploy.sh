#!/bin/bash
# scripts/deploy.sh
# Complete deployment script for EVENTIX

set -e

echo "🚀 Starting EVENTIX Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker Desktop."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker Desktop."
        exit 1
    fi
    
    print_success "Prerequisites check passed!"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        print_status "Creating default .env file..."
        cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://eventix_user:eventix_password@eventix-db:5432/eventix
REDIS_URL=redis://redis:6379

# Security Configuration
JWT_SECRET_KEY=eventix-super-secret-jwt-key-change-in-production-$(date +%s)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service URLs
USER_SERVICE_URL=http://user-service:8000
EVENT_SERVICE_URL=http://event-service:8001
BOOKING_SERVICE_URL=http://booking-service:8002
PAYMENT_SERVICE_URL=http://payment-service:8003

# Payment Gateway (for testing)
STRIPE_SECRET_KEY=sk_test_51234567890abcdef
STRIPE_PUBLISHABLE_KEY=pk_test_51234567890abcdef

# Environment
ENVIRONMENT=production
RATE_LIMIT_PER_MINUTE=100

# Monitoring
GF_SECURITY_ADMIN_PASSWORD=admin123
EOF
        print_success "Environment file created!"
    else
        print_warning ".env file already exists, using existing configuration"
    fi
}

# Deploy services
deploy_services() {
    print_status "Deploying EVENTIX services..."
    
    # Stop any existing containers
    print_status "Stopping existing containers..."
    docker-compose down -v 2>/dev/null || true
    
    # Pull latest images and build
    print_status "Building and starting services..."
    docker-compose up --build -d
    
    print_success "Services deployment initiated!"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be healthy..."
    
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost/health > /dev/null 2>&1; then
            print_success "All services are healthy!"
            return 0
        fi
        
        echo -n "."
        sleep 5
        ((attempt++))
    done
    
    print_error "Services failed to become healthy within timeout"
    return 1
}

# Initialize sample data
initialize_data() {
    print_status "Initializing sample data..."
    
    # Wait for API Gateway to be ready
    sleep 10
    
    # Create admin user
    print_status "Creating admin user..."
    curl -s -X POST http://localhost/api/v1/auth/register \
        -H "Content-Type: application/json" \
        -d '{
            "email": "admin@eventix.com",
            "password": "admin123",
            "first_name": "Admin",
            "last_name": "User",
            "is_admin": true
        }' > /dev/null 2>&1 || print_warning "Admin user might already exist"
    
    # Create sample user
    print_status "Creating sample user..."
    curl -s -X POST http://localhost/api/v1/auth/register \
        -H "Content-Type: application/json" \
        -d '{
            "email": "user@eventix.com",
            "password": "user123",
            "first_name": "John",
            "last_name": "Doe"
        }' > /dev/null 2>&1 || print_warning "Sample user might already exist"
    
    print_success "Sample data initialized!"
}

# Display deployment summary
show_summary() {
    print_success "🎉 EVENTIX Deployment Complete!"
    echo ""
    echo "📊 System Access URLs:"
    echo "   🌐 Main Application:     http://localhost"
    echo "   📖 API Documentation:   http://localhost/docs"
    echo "   📈 Monitoring Dashboard: http://localhost:3000"
    echo "   🔍 Metrics (Prometheus): http://localhost:9090"
    echo ""
    echo "🔐 Default Credentials:"
    echo "   👤 Admin User:     admin@eventix.com / admin123"
    echo "   👤 Sample User:    user@eventix.com / user123"
    echo "   📊 Grafana:       admin / admin123"
    echo ""
    echo "🛠️ Management Commands:"
    echo "   ✅ Health Check:    curl http://localhost/health"
    echo "   📊 View Logs:       docker-compose logs -f"
    echo "   🛑 Stop Services:   docker-compose down"
    echo "   🔄 Restart:         docker-compose restart"
    echo ""
    print_status "System is ready for use!"
}

# Main deployment flow
main() {
    echo "==============================================="
    echo "🎫 EVENTIX - Cloud Native Deployment Script"
    echo "==============================================="
    echo ""
    
    check_prerequisites
    setup_environment
    deploy_services
    wait_for_services
    initialize_data
    show_summary
}

# Handle script interruption
cleanup() {
    print_warning "Deployment interrupted!"
    print_status "Cleaning up..."
    docker-compose down 2>/dev/null || true
    exit 1
}

trap cleanup INT

# Run main function
main "$@"