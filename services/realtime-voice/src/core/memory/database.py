"""
Database Connection and Migration Management
"""
import logging
import asyncio
from typing import Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from src.config import settings
from src.core.memory.models import Base

logger = logging.getLogger(__name__)

class Database:
    """Database connection manager"""
    
    def __init__(self):
        """Initialize database connection manager"""
        self.engine: Optional[AsyncEngine] = None
        self.async_session: Optional[sessionmaker] = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize database connection"""
        if self.initialized:
            return True
            
        try:
            # Check if DATABASE_URL is provided (for Docker deployment)
            import os
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                # Convert PostgreSQL URL to asyncpg
                if database_url.startswith("postgresql://"):
                    db_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
                else:
                    db_url = database_url
            else:
                # Create database URL from individual settings
                db_url = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            
            # Create engine
            self.engine = create_async_engine(
                db_url,
                echo=settings.DEBUG,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
            )
            
            # Create session factory
            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                
            logger.info("Database connection successful")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            return False
    
    async def create_tables(self) -> bool:
        """Create database tables"""
        if not self.initialized or not self.engine:
            logger.error("Database not initialized")
            return False
            
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
            logger.info("Database tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            return False
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if not self.initialized or not self.async_session:
            raise RuntimeError("Database not initialized")
            
        async with self.async_session() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise e
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.initialized = False
            logger.info("Database connection closed")


# Create singleton instance
database = Database()