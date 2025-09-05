import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional, Any
import aio_pika
from aio_pika import connect_robust, ExchangeType, Message
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractExchange
import os
from datetime import datetime
from mode import production
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self):
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.exchanges: Dict[str, AbstractExchange] = {}
        self.consumers: Dict[str, Callable] = {}
        self.is_connected = False
        if production:
            self.rabbitmq_url = 'amqp://eventix:eventix123@rabbitmq:5672/'
        else:
            self.rabbitmq_url = 'amqp://eventix:eventix123@localhost:5672/'

    async def connect(self) -> None:
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            self.is_connected = True
            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            self.is_connected = False
            logger.info("Disconnected from RabbitMQ")

    async def declare_exchange(
        self, 
        exchange_name: str, 
        exchange_type: ExchangeType = ExchangeType.TOPIC,
        durable: bool = True
    ) -> AbstractExchange:
        """Declare an exchange"""
        if not self.is_connected:
            await self.connect()
        
        exchange = await self.channel.declare_exchange(
            exchange_name, 
            exchange_type, 
            durable=durable
        )
        self.exchanges[exchange_name] = exchange
        return exchange

    async def declare_queue(
        self, 
        queue_name: str, 
        durable: bool = True,
        exclusive: bool = False
    ):
        """Declare a queue"""
        if not self.is_connected:
            await self.connect()
        
        return await self.channel.declare_queue(
            queue_name, 
            durable=durable,
            exclusive=exclusive
        )

    async def publish_message(
        self, 
        exchange_name: str, 
        routing_key: str, 
        message: Dict[str, Any],
        message_id: str = None,
        correlation_id: str = None
    ) -> None:
        """Publish a message to an exchange"""
        if not self.is_connected:
            await self.connect()
        
        if exchange_name not in self.exchanges:
            await self.declare_exchange(exchange_name)
        
        exchange = self.exchanges[exchange_name]
        
        message_body = json.dumps(message, default=str).encode('utf-8')
        
        aio_message = Message(
            message_body,
            message_id=message_id,
            correlation_id=correlation_id,
            content_type='application/json'
        )
        
        await exchange.publish(aio_message, routing_key=routing_key)
        logger.info(f"Published message to {exchange_name} with routing key {routing_key}")

    async def subscribe_to_queue(
        self, 
        queue_name: str, 
        callback: Callable,
        exchange_name: str = None,
        routing_key: str = None
    ) -> None:
        """Subscribe to a queue and bind to exchange if provided"""
        if not self.is_connected:
            await self.connect()
        
        queue = await self.declare_queue(queue_name)
        
        if exchange_name and routing_key:
            if exchange_name not in self.exchanges:
                await self.declare_exchange(exchange_name)
            
            await queue.bind(self.exchanges[exchange_name], routing_key=routing_key)
        
        async def message_handler(message):
            async with message.process():
                try:
                    body = json.loads(message.body.decode('utf-8'))
                    await callback(body, message)
                    logger.info(f"Successfully processed message from {queue_name}")
                except Exception as e:
                    logger.error(f"Error processing message from {queue_name}: {e}")
                    raise
        
        await queue.consume(message_handler)
        logger.info(f"Subscribed to queue: {queue_name}")

    @asynccontextmanager
    async def connection_context(self):
        """Context manager for RabbitMQ connection"""
        await self.connect()
        try:
            yield self
        finally:
            await self.disconnect()

# Global RabbitMQ client instance
rabbitmq_client = RabbitMQClient()