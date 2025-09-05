import asyncio
import aiohttp
from typing import Dict, List
from shared.rabbitmq_client import rabbitmq_client

class HealthChecker:
    """Health check utilities for microservices"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name

    async def check_rabbitmq_health(self) -> Dict[str, str]:
        """Check RabbitMQ connection health"""
        try:
            if rabbitmq_client.is_connected:
                return {"status": "healthy", "service": "rabbitmq"}
            else:
                await rabbitmq_client.connect()
                return {"status": "healthy", "service": "rabbitmq"}
        except Exception as e:
            return {"status": "unhealthy", "service": "rabbitmq", "error": str(e)}

    async def check_database_health(self, database_url: str) -> Dict[str, str]:
        """Check database connection health"""
        try:
            # This would use your database connection
            return {"status": "healthy", "service": "database"}
        except Exception as e:
            return {"status": "unhealthy", "service": "database", "error": str(e)}

    async def check_external_service(self, service_url: str, service_name: str) -> Dict[str, str]:
        """Check external service health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{service_url}/health", timeout=5) as response:
                    if response.status == 200:
                        return {"status": "healthy", "service": service_name}
                    else:
                        return {"status": "unhealthy", "service": service_name, "status_code": response.status}
        except Exception as e:
            return {"status": "unhealthy", "service": service_name, "error": str(e)}

    async def comprehensive_health_check(self, dependencies: List[Dict[str, str]]) -> Dict[str, any]:
        """Perform comprehensive health check"""
        results = {
            "service": self.service_name,
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "dependencies": {}
        }
        
        # Check RabbitMQ
        rabbitmq_health = await self.check_rabbitmq_health()
        results["dependencies"]["rabbitmq"] = rabbitmq_health
        
        # Check other dependencies
        for dep in dependencies:
            if dep["type"] == "database":
                health = await self.check_database_health(dep["url"])
            elif dep["type"] == "service":
                health = await self.check_external_service(dep["url"], dep["name"])
            
            results["dependencies"][dep["name"]] = health
            
            if health["status"] != "healthy":
                results["status"] = "degraded"
        
        return results