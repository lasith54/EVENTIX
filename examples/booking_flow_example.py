import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import httpx
from shared.rabbitmq_client import rabbitmq_client
from shared.event_handler import BaseEventHandler
from shared.event_schemas import EventType

class BookingFlowListener(BaseEventHandler):
    
    def __init__(self):
        super().__init__("booking-flow-listener")
        self.events_received = []

    async def setup_handlers(self):
        self.register_handler(EventType.BOOKING_INITIATED, self.log_event)
        self.register_handler(EventType.SEAT_RESERVED, self.log_event)
        self.register_handler(EventType.PAYMENT_COMPLETED, self.log_event)
        self.register_handler(EventType.BOOKING_CONFIRMED, self.log_event)
        self.register_handler(EventType.EMAIL_NOTIFICATION, self.log_event)

    async def log_event(self, event):
        self.events_received.append({
            'event_type': event.event_type,
            'timestamp': event.timestamp,
            'service': event.service_name,
            'data': event.data
        })
        print(f"📧 Received event: {event.event_type} from {event.service_name}")

async def register_test_user():
    """Register a test user for authentication"""
    async with httpx.AsyncClient() as client:
        register_data = {
            "email": "test_user@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "test_password",
            "phone_number": "1234567890"
        }
        
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/auth/register",
                json=register_data
            )
            
            if response.status_code in [200, 201]:
                print("User registered successfully")
                return True
            elif response.status_code == 409:
                print("User already exists, continuing...")
                return True
            else:
                print(f"Registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Auth service not available for registration: {e}")
            return False

async def get_auth_token():
    """Get authentication token from auth service"""
    async with httpx.AsyncClient() as client:
        auth_data = {
            "username": "test_user@example.com",
            "password": "test_password"
        }
        
        try:
            # Check if auth service is running on a different port
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token') or token_data.get('token')
            else:
                print(f"Auth failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Auth service not available: {e}")
            return None

async def simulate_booking_flow():
    """Simulate a complete booking flow"""
    
    # Setup event listener
    listener = BookingFlowListener()
    rabbitmq_client.rabbitmq_url = 'amqp://eventix:eventix123@localhost:5672/'
    await rabbitmq_client.connect()
    await listener.setup_handlers()
    
    # Start listening in background
    consume_task = asyncio.create_task(listener.start_consuming())
    
    # Wait a moment for listener to be ready
    await asyncio.sleep(2)

    # Register test user first
    print("🔐 Registering test user...")
    registration_success = await register_test_user()
    
    # Get authentication token
    print("🔑 Getting authentication token...")
    auth_token = await get_auth_token()

    if not auth_token:
        print("Cannot proceed without authentication token")
        consume_task.cancel()
        await rabbitmq_client.disconnect()
        return
    
    # Simulate booking creation via API
    async with httpx.AsyncClient() as client:
        booking_data = {
            "event_id": "ab89926f-276c-4e8e-8be0-af2de60ac6e3",
            "total_amount": 200.0,
            "customer_email": "test_user@example.com",
            "customer_name": "Test User",
            "items": [
                {"seat_id": "64091697-b964-49c3-8949-d2339ef0cdbb", "venue_section_id": "f88d2b0d-d73e-4c30-a982-5f251ba2622e", "unit_price": 100, "quantity": 1, "section_name": "VIP"},
                {"seat_id": "efdedd1f-26b9-4200-b0ba-e3cb05f96a8a", "venue_section_id": "f88d2b0d-d73e-4c30-a982-5f251ba2622e", "unit_price": 100, "quantity": 1, "section_name": "VIP"}
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
        
        response = await client.post(
            "http://localhost:8002/api/v1/bookings/create",
            json=booking_data,
            headers=headers
        )
        
        print(f"🎫 Booking created: {response.json()}")
    
    # Wait for events to be processed
    await asyncio.sleep(10)
    
    # Print all received events
    print("\n📋 Events received during booking flow:")
    for event in listener.events_received:
        print(f"  - {event['event_type']} ({event['service']}) at {event['timestamp']}")
    
    # Cleanup
    consume_task.cancel()
    await rabbitmq_client.disconnect()

if __name__ == "__main__":
    asyncio.run(simulate_booking_flow())