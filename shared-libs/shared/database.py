"""Database connection and session management."""

from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from shared.config import DatabaseSettings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self, settings: DatabaseSettings):
        """Initialize database manager.
        
        Args:
            settings: Database settings
        """
        self.settings = settings
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
    
    def get_engine(self) -> AsyncEngine:
        """Get or create database engine.
        
        Returns:
            AsyncEngine instance
        """
        if self._engine is None:
            self._engine = create_async_engine(
                self.settings.url,
                echo=self.settings.echo,
                pool_size=self.settings.pool_size,
                max_overflow=self.settings.max_overflow,
                poolclass=NullPool if "sqlite" in self.settings.url else None,
            )
        return self._engine
    
    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create session factory.
        
        Returns:
            Session factory
        """
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.get_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._session_factory
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager.
        
        Yields:
            AsyncSession instance
        """
        session_factory = self.get_session_factory()
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def create_tables(self):
        """Create all database tables."""
        engine = self.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self):
        """Drop all database tables."""
        engine = self.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def close(self):
        """Close database connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Global database manager instance
_db_manager: DatabaseManager | None = None


def init_db(settings: DatabaseSettings) -> DatabaseManager:
    """Initialize global database manager.
    
    Args:
        settings: Database settings
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    _db_manager = DatabaseManager(settings)
    return _db_manager


def get_db_manager() -> DatabaseManager:
    """Get global database manager.
    
    Returns:
        DatabaseManager instance
        
    Raises:
        RuntimeError: If database not initialized
    """
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection.
    
    Yields:
        AsyncSession instance
    """
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        yield session
