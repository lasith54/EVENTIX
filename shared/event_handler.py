import logging
from typing import Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseEventHandler(ABC):
    def __init__(self, service_name: str):
        self.service_name = service_name

    async def handle_event(self, routing_key: str, event_data: Dict[str, Any]):
        """Main event handler that routes to specific handlers"""
        try:
            event_type = routing_key.split('.')[-1]
            domain = routing_key.split('.')[0]
            
            logger.info(f"[{self.service_name}] Handling {domain}.{event_type} event")
            
            if domain == "user":
                await self.handle_user_event(event_type, event_data)
            elif domain == "event":
                await self.handle_event_event(event_type, event_data)
            elif domain == "booking":
                await self.handle_booking_event(event_type, event_data)
            elif domain == "payment":
                await self.handle_payment_event(event_type, event_data)
            else:
                logger.warning(f"Unknown event domain: {domain}")
                
        except Exception as e:
            logger.error(f"Error handling event {routing_key}: {e}")
            raise

    @abstractmethod
    async def handle_user_event(self, event_type: str, event_data: Dict[str, Any]):
        pass

    @abstractmethod
    async def handle_event_event(self, event_type: str, event_data: Dict[str, Any]):
        pass

    @abstractmethod
    async def handle_booking_event(self, event_type: str, event_data: Dict[str, Any]):
        pass

    @abstractmethod
    async def handle_payment_event(self, event_type: str, event_data: Dict[str, Any]):
        pass