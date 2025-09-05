import asyncio
import logging
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod
from .rabbitmq_client import rabbitmq_client
from .event_schemas import BaseEvent, EventType

logger = logging.getLogger(__name__)

class BaseEventHandler(ABC):
    """Base class for event handlers"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.exchange_name = "eventix.events"
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, event_type: EventType, handler: Callable):
        """Register an event handler"""
        self.handlers[event_type.value] = handler
        logger.info(f"Registered handler for event type: {event_type.value}")

    async def handle_event(self, message_body: Dict[str, Any], message) -> None:
        """Handle incoming event message"""
        try:
            event = BaseEvent(**message_body)
            handler = self.handlers.get(event.event_type.value)
            
            if handler:
                await handler(event)
                logger.info(f"Successfully handled event: {event.event_type.value}")
            else:
                logger.warning(f"No handler found for event type: {event.event_type.value}")
                
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            raise

    async def start_consuming(self):
        """Start consuming events from RabbitMQ"""
        queue_name = f"{self.service_name}.events"
        
        for event_type in self.handlers.keys():
            await rabbitmq_client.subscribe_to_queue(
                queue_name=f"{queue_name}.{event_type}",
                callback=self.handle_event,
                exchange_name=self.exchange_name,
                routing_key=event_type
            )
        
        logger.info(f"Started consuming events for service: {self.service_name}")

    @abstractmethod
    async def setup_handlers(self):
        """Setup event handlers - to be implemented by each service"""
        pass

class SagaOrchestrator:
    """
    Saga pattern implementation for distributed transactions
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.saga_steps: Dict[str, list] = {}
        self.compensation_steps: Dict[str, list] = {}

    def define_saga(self, saga_id: str, steps: list, compensations: list):
        """Define a saga with its steps and compensations"""
        self.saga_steps[saga_id] = steps
        self.compensation_steps[saga_id] = compensations

    async def execute_saga(self, saga_id: str, context: Dict[str, Any]):
        """Execute a saga"""
        steps = self.saga_steps.get(saga_id, [])
        executed_steps = []
        
        try:
            for step in steps:
                await step(context)
                executed_steps.append(step)
                
            logger.info(f"Saga {saga_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Saga {saga_id} failed at step {len(executed_steps)}: {e}")
            await self._compensate(saga_id, executed_steps, context)
            return False

    async def _compensate(self, saga_id: str, executed_steps: list, context: Dict[str, Any]):
        """Execute compensation steps"""
        compensations = self.compensation_steps.get(saga_id, [])
        
        for i, step in enumerate(reversed(executed_steps)):
            try:
                if i < len(compensations):
                    await compensations[i](context)
                    logger.info(f"Compensation step {i} executed for saga {saga_id}")
            except Exception as e:
                logger.error(f"Compensation failed for saga {saga_id}: {e}")