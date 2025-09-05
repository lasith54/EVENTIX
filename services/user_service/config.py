from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # API
    api_title: str = Field(default="User Service API", description="API Title")
    api_version: str = Field(default="1.0.0", description="API Version")
    debug: bool = Field(default=True, description="Debug mode")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Host")
    port: int = Field(default=8000, description="Port")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()