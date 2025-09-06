#!/bin/bash
# filepath: e:\Eventix\run-k8s.sh

# Parse command line arguments
SKIP_BUILD=false
SKIP_DEPLOY=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-deploy)
            SKIP_DEPLOY=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            echo "Unknown option $1"
            echo "Usage: $0 [--skip-build] [--skip-deploy] [--clean]"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Eventix Kubernetes Deployment Script${NC}"
echo -e "${GREEN}=======================================${NC}"

# Check if minikube is running
check_minikube() {
    if minikube status 2>/dev/null | grep -q "Running"; then
        return 0
    else
        return 1
    fi
}

# Clean up function
clean_deployment() {
    echo -e "${YELLOW}🧹 Cleaning up existing deployment...${NC}"
    kubectl delete namespace eventix --ignore-not-found=true >/dev/null 2>&1
    sleep 5
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Build Docker images
build_images() {
    echo -e "${CYAN}🔨 Building Docker images...${NC}"
    
    # Configure Docker to use Minikube's Docker daemon
    eval $(minikube docker-env)
    
    echo -e "${YELLOW}Building API Gateway...${NC}"
    docker build -f services/api-gateway/Dockerfile -t eventix/api-gateway:latest . >/dev/null 2>&1
    
    echo -e "${YELLOW}Building User Service...${NC}"
    docker build -f services/user_service/Dockerfile -t eventix/user-service:latest . >/dev/null 2>&1
    
    echo -e "${YELLOW}Building Event Service...${NC}"
    docker build -f services/event_service/Dockerfile -t eventix/event-service:latest . >/dev/null 2>&1
    
    echo -e "${YELLOW}Building Booking Service...${NC}"
    docker build -f services/booking_service/Dockerfile -t eventix/booking-service:latest . >/dev/null 2>&1
    
    echo -e "${YELLOW}Building Payment Service...${NC}"
    if [ -f "services/payment_service/Dockerfile" ]; then
        docker build -f services/payment_service/Dockerfile -t eventix/payment-service:latest . >/dev/null 2>&1
    fi
    
    echo -e "${YELLOW}Building Frontend...${NC}"
    docker build -f frontend/Dockerfile -t eventix/frontend:latest ./frontend >/dev/null 2>&1
    
    echo -e "${GREEN}✅ All images built successfully${NC}"
}

# Deploy to Kubernetes
deploy_to_kubernetes() {
    echo -e "${CYAN}🚀 Deploying to Kubernetes...${NC}"
    
    # Create namespace
    echo -e "${YELLOW}Creating namespace...${NC}"
    kubectl create namespace eventix --dry-run=client -o yaml | kubectl apply -f - >/dev/null 2>&1
    
    # Deploy databases first
    echo -e "${YELLOW}Deploying databases...${NC}"
    kubectl apply -f k8s/databases.yaml
    
    # Wait for databases to be ready
    echo -e "${YELLOW}Waiting for databases to be ready...${NC}"
    kubectl wait --for=condition=available deployment/user-db -n eventix --timeout=300s >/dev/null 2>&1 &
    kubectl wait --for=condition=available deployment/event-db -n eventix --timeout=300s >/dev/null 2>&1 &
    kubectl wait --for=condition=available deployment/booking-db -n eventix --timeout=300s >/dev/null 2>&1 &
    kubectl wait --for=condition=available deployment/payment-db -n eventix --timeout=300s >/dev/null 2>&1 &
    wait
    
    # Deploy RabbitMQ if exists
    if [ -f "k8s/rabbitmq.yaml" ]; then
        echo -e "${YELLOW}Deploying RabbitMQ...${NC}"
        kubectl apply -f k8s/rabbitmq.yaml >/dev/null 2>&1
    fi
    
    # Deploy services
    echo -e "${YELLOW}Deploying services...${NC}"
    [ -f "k8s/user-service.yaml" ] && kubectl apply -f k8s/user-service.yaml >/dev/null 2>&1
    [ -f "k8s/event-service.yaml" ] && kubectl apply -f k8s/event-service.yaml >/dev/null 2>&1
    [ -f "k8s/booking-service.yaml" ] && kubectl apply -f k8s/booking-service.yaml >/dev/null 2>&1
    [ -f "k8s/payment-service.yaml" ] && kubectl apply -f k8s/payment-service.yaml >/dev/null 2>&1
    
    # Deploy API Gateway
    echo -e "${YELLOW}Deploying API Gateway...${NC}"
    kubectl apply -f k8s/api-gateway.yaml >/dev/null 2>&1
    
    # Deploy Frontend using existing yaml file
    echo -e "${YELLOW}Deploying Frontend...${NC}"
    kubectl apply -f k8s/frontend.yaml >/dev/null 2>&1
    
    echo -e "${GREEN}✅ Deployment completed${NC}"
}

# Kill existing port forwards (cross-platform)
kill_port_forwards() {
    # Try different methods to kill kubectl port-forward processes
    if command -v pkill >/dev/null 2>&1; then
        pkill -f "kubectl port-forward" >/dev/null 2>&1
    elif command -v taskkill >/dev/null 2>&1; then
        # Windows
        taskkill //F //IM kubectl.exe >/dev/null 2>&1
    else
        # Fallback - try to find and kill processes
        ps aux 2>/dev/null | grep "kubectl port-forward" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    fi
}

# Check if port forwards are running (cross-platform)
check_port_forwards() {
    if command -v pgrep >/dev/null 2>&1; then
        pgrep -f "kubectl port-forward" >/dev/null 2>&1
    elif command -v tasklist >/dev/null 2>&1; then
        # Windows
        tasklist 2>/dev/null | grep -i kubectl >/dev/null 2>&1
    else
        # Fallback
        ps aux 2>/dev/null | grep "kubectl port-forward" | grep -v grep >/dev/null 2>&1
    fi
}

# Setup port forwarding
start_port_forwarding() {
    echo -e "${CYAN}🔌 Setting up port forwarding...${NC}"
    
    # Kill existing port forwards
    kill_port_forwards
    sleep 2
    
    # Store background job PIDs
    PORT_FORWARD_PIDS=()
    
    # Frontend
    kubectl port-forward -n eventix svc/frontend 3000:3000 >/dev/null 2>&1 &
    PORT_FORWARD_PIDS+=($!)
    echo -e "${GREEN}✅ Frontend -> http://localhost:3000${NC}"
    
    # API Gateway
    kubectl port-forward -n eventix svc/api-gateway 8080:8080 >/dev/null 2>&1 &
    PORT_FORWARD_PIDS+=($!)
    echo -e "${GREEN}✅ API Gateway -> http://localhost:8080${NC}"
    
    # Services (if they exist)
    services=("user-service:8000" "event-service:8001" "booking-service:8002" "payment-service:8003")
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name port <<< "$service_info"
        if kubectl get svc "$service_name" -n eventix >/dev/null 2>&1; then
            kubectl port-forward -n eventix svc/"$service_name" "$port:$port" >/dev/null 2>&1 &
            PORT_FORWARD_PIDS+=($!)
            echo -e "${GREEN}✅ $service_name -> http://localhost:$port${NC}"
        fi
    done
    
    # Databases
    databases=("user-db:5432:5432" "event-db:5433:5432" "booking-db:5434:5432" "payment-db:5435:5432")
    
    for db_info in "${databases[@]}"; do
        IFS=':' read -r db_name port target <<< "$db_info"
        kubectl port-forward -n eventix svc/"$db_name" "$port:$target" >/dev/null 2>&1 &
        PORT_FORWARD_PIDS+=($!)
        echo -e "${GREEN}✅ $db_name -> localhost:$port${NC}"
    done
    
    # RabbitMQ (if exists)
    if kubectl get svc rabbitmq -n eventix >/dev/null 2>&1; then
        kubectl port-forward -n eventix svc/rabbitmq 5672:5672 >/dev/null 2>&1 &
        PORT_FORWARD_PIDS+=($!)
        kubectl port-forward -n eventix svc/rabbitmq 15672:15672 >/dev/null 2>&1 &
        PORT_FORWARD_PIDS+=($!)
        echo -e "${GREEN}✅ RabbitMQ -> localhost:5672 (AMQP)${NC}"
        echo -e "${GREEN}✅ RabbitMQ Management -> http://localhost:15672${NC}"
    fi
}

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping all port forwards...${NC}"
    
    # Kill all background jobs
    for pid in "${PORT_FORWARD_PIDS[@]}"; do
        kill $pid 2>/dev/null || true
    done
    
    # Additional cleanup
    kill_port_forwards
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Main execution
main() {
    # Check if minikube is running
    if ! check_minikube; then
        echo -e "${RED}❌ Minikube is not running. Please start minikube first:${NC}"
        echo -e "${YELLOW}   minikube start --driver=docker --memory=4096 --cpus=4${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Minikube is running${NC}"
    
    # Clean up if requested
    if [ "$CLEAN" = true ]; then
        clean_deployment
    fi
    
    # Build images unless skipped
    if [ "$SKIP_BUILD" = false ]; then
        build_images
    else
        echo -e "${YELLOW}⏭️  Skipping image build${NC}"
    fi
    
    # Deploy to Kubernetes unless skipped
    if [ "$SKIP_DEPLOY" = false ]; then
        deploy_to_kubernetes
        
        # Wait a moment for services to start
        echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
        sleep 20
    else
        echo -e "${YELLOW}⏭️  Skipping deployment${NC}"
    fi
    
    # Start port forwarding
    start_port_forwarding
    
    echo ""
    echo -e "${GREEN}🎉 Eventix is now running!${NC}"
    echo -e "${GREEN}=========================${NC}"
    echo -e "${CYAN}Frontend:     http://localhost:3000${NC}"
    echo -e "${CYAN}API Gateway:  http://localhost:8080${NC}"
    echo ""
    echo -e "${CYAN}Services:${NC}"
    echo -e "${WHITE}User:         http://localhost:8000${NC}"
    echo -e "${WHITE}Event:        http://localhost:8001${NC}"
    echo -e "${WHITE}Booking:      http://localhost:8002${NC}"
    echo -e "${WHITE}Payment:      http://localhost:8003${NC}"
    echo ""
    echo -e "${CYAN}Database Connections:${NC}"
    echo -e "${WHITE}User DB:      localhost:5432${NC}"
    echo -e "${WHITE}Event DB:     localhost:5433${NC}"
    echo -e "${WHITE}Booking DB:   localhost:5434${NC}"
    echo -e "${WHITE}Payment DB:   localhost:5435${NC}"
    echo ""
    echo -e "${YELLOW}💡 Make sure your frontend .env file uses:${NC}"
    echo -e "${WHITE}   VITE_API_BASE_URL=http://localhost:8080/api/v1${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all port forwards and exit${NC}"
    echo ""
    
    # Keep script running and monitor port forwards
    while true; do
        sleep 10
        
        # Check if any of our specific PIDs are still running
        running_count=0
        for pid in "${PORT_FORWARD_PIDS[@]}"; do
            if kill -0 $pid 2>/dev/null; then
                running_count=$((running_count + 1))
            fi
        done
        
        if [ $running_count -eq 0 ]; then
            echo -e "${RED}⚠️  All port forwards have stopped${NC}"
            break
        fi
    done
}

# Run main function
main "$@"