import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType
from aio_pika.abc import AbstractIncomingMessage
import os
from datetime import datetime
from mode import production

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchanges: Dict[str, aio_pika.Exchange] = {}
        self.queues: Dict[str, aio_pika.Queue] = {}
        if production:
            self.url = os.getenv('RABBITMQ_URL', 'amqp://eventix:eventix123@rabbitmq:5672/')
        else:
            self.url = os.getenv('RABBITMQ_URL', 'amqp://eventix:eventix123@localhost:5672/')

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(self.url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            logger.info("Connected to RabbitMQ successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

    async def disconnect(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def setup_exchanges_and_queues(self, service_name: str):
        """Setup exchanges and queues for the service"""
        # Declare topic exchanges
        exchanges = ["user.events", "event.events", "booking.events", "payment.events"]
        for exchange_name in exchanges:
            exchange = await self.channel.declare_exchange(
                exchange_name, ExchangeType.TOPIC, durable=True
            )
            self.exchanges[exchange_name] = exchange
            logger.info(f"Declared exchange: {exchange_name}")

        # Declare service queue
        queue_name = f"{service_name}.queue"
        queue = await self.channel.declare_queue(queue_name, durable=True)
        self.queues[queue_name] = queue
        logger.info(f"Declared queue: {queue_name}")

        # Setup bindings based on service
        await self._setup_bindings(service_name, queue_name)

    async def _setup_bindings(self, service_name: str, queue_name: str):
        """Setup queue bindings based on service requirements"""
        bindings = {
            "user-service": [
                ("booking.events", "booking.*"),
                ("payment.events", "payment.*")
            ],
            "event-service": [
                ("user.events", "user.*"),
                ("booking.events", "booking.*"),
                ("payment.events", "payment.*")
            ],
            "booking-service": [
                ("user.events", "user.*"),
                ("event.events", "event.*"),
                ("payment.events", "payment.*")
            ],
            "payment-service": [
                ("booking.events", "booking.*"),
                ("event.events", "event.*")
            ]
        }

        if service_name in bindings:
            for exchange_name, routing_key in bindings[service_name]:
                await self.queues[queue_name].bind(
                    self.exchanges[exchange_name], routing_key=routing_key
                )
                logger.info(f"Bound {queue_name} to {exchange_name} with {routing_key}")

    async def publish_event(self, exchange_name: str, routing_key: str, event_data: Dict[str, Any]):
        """Publish an event to RabbitMQ"""
        if exchange_name not in self.exchanges:
            exchange = await self.channel.declare_exchange(
                exchange_name, ExchangeType.TOPIC, durable=True
            )
            self.exchanges[exchange_name] = exchange

        # Add metadata to event
        event_data.update({
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": event_data.get("event_id", f"evt_{int(datetime.utcnow().timestamp())}")
        })

        message_body = json.dumps(event_data).encode()
        message = Message(
            message_body,
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
            headers={
                "service": event_data.get("service", "unknown"),
                "event_type": routing_key,
                "timestamp": event_data.get("timestamp"),
            }
        )

        await self.exchanges[exchange_name].publish(message, routing_key=routing_key)
        logger.info(f"Published event {routing_key} to exchange {exchange_name}")

    async def start_consuming(self, service_name: str, callback: Callable):
        """Start consuming events from the service queue"""
        queue_name = f"{service_name}.queue"
        
        async def process_message(message: AbstractIncomingMessage):
            try:
                async with message.process():
                    event_data = json.loads(message.body.decode())
                    logger.info(f"[{service_name}] Received event: {message.routing_key}")
                    await callback(message.routing_key, event_data)
            except Exception as e:
                logger.error(f"Error processing message in {service_name}: {e}")

        await self.queues[queue_name].consume(process_message)
        logger.info(f"Started consuming events for {service_name}")

# Global client instance
rabbitmq_client = RabbitMQClient()