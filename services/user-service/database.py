import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from mode import production

if production:
    engine = create_engine('postgresql+psycopg2://postgres:postgres@user-db:5432/user-db', echo=True, future=True)
else:
    engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/user-db', echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if production:
    async_engine = create_async_engine('postgresql+asyncpg://postgres:postgres@user-db:5432/user-db', echo=True, future=True)
else:
    async_engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/user-db', echo=True, future=True)

AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()