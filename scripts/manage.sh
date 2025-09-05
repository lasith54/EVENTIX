#!/bin/bash
# scripts/manage.sh
# Service management script

set -e

COMMAND=$1
SERVICE=$2

usage() {
    echo "Usage: $0 {start|stop|restart|logs|scale|status} [service]"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services or specific service"
    echo "  stop      - Stop all services or specific service"
    echo "  restart   - Restart all services or specific service"
    echo "  logs      - View logs for all services or specific service"
    echo "  scale     - Scale services (requires additional parameters)"
    echo "  status    - Show status of all services"
    echo ""
    echo "Services:"
    echo "  user-service, event-service, booking-service, payment-service"
    echo "  api-gateway, eventix-db, redis, nginx, grafana, prometheus"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start all services"
    echo "  $0 stop user-service        # Stop user service"
    echo "  $0 logs api-gateway         # View API gateway logs"
    echo "  $0 scale user-service=3     # Scale user service to 3 instances"
}

case $COMMAND in
    start)
        if [ -z "$SERVICE" ]; then
            echo "🚀 Starting all EVENTIX services..."
            docker-compose up -d
        else
            echo "🚀 Starting $SERVICE..."
            docker-compose up -d "$SERVICE"
        fi
        ;;
    stop)
        if [ -z "$SERVICE" ]; then
            echo "🛑 Stopping all EVENTIX services..."
            docker-compose down
        else
            echo "🛑 Stopping $SERVICE..."
            docker-compose stop "$SERVICE"
        fi
        ;;
    restart)
        if [ -z "$SERVICE" ]; then
            echo "🔄 Restarting all EVENTIX services..."
            docker-compose restart
        else
            echo "🔄 Restarting $SERVICE..."
            docker-compose restart "$SERVICE"
        fi
        ;;
    logs)
        if [ -z "$SERVICE" ]; then
            echo "📜 Showing logs for all services..."
            docker-compose logs -f
        else
            echo "📜 Showing logs for $SERVICE..."
            docker-compose logs -f "$SERVICE"
        fi
        ;;
    scale)
        if [ -z "$SERVICE" ]; then
            echo "⚖️ Scaling services with default configuration..."
            docker-compose up -d --scale user-service=2 --scale event-service=2 --scale booking-service=2 --scale payment-service=2
        else
            echo "⚖️ Scaling $SERVICE..."
            docker-compose up -d --scale "$SERVICE"
        fi
        ;;
    status)
        echo "📊 EVENTIX Service Status:"
        docker-compose ps
        ;;
    *)
        usage
        exit 1
        ;;
esac

---
