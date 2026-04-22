#!/usr/bin/env python3
"""Verification script for Phase 1 setup."""

import sys
import asyncio
from typing import Tuple

def check_imports() -> Tuple[bool, str]:
    """Check if shared libraries can be imported."""
    try:
        from shared.config import get_settings
        from shared.database import init_db
        from shared.models import Tenant, User, Investigation
        from shared.events import EventProducer, AlertEvent
        from shared.auth import create_access_token
        from shared.logging import setup_logging, get_logger
        return True, "✓ All shared libraries imported successfully"
    except ImportError as e:
        return False, f"✗ Import error: {e}"


async def check_database() -> Tuple[bool, str]:
    """Check database connection."""
    try:
        from shared.config import get_settings
        from shared.database import init_db
        from sqlalchemy import text
        
        settings = get_settings()
        db_manager = init_db(settings.database)
        
        async with db_manager.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        
        await db_manager.close()
        return True, "✓ Database connection successful"
    except Exception as e:
        return False, f"✗ Database connection failed: {e}"


def check_redis() -> Tuple[bool, str]:
    """Check Redis connection."""
    try:
        import redis
        from shared.config import get_settings
        
        settings = get_settings()
        r = redis.from_url(settings.redis.url)
        r.ping()
        r.close()
        return True, "✓ Redis connection successful"
    except Exception as e:
        return False, f"✗ Redis connection failed: {e}"


def check_kafka() -> Tuple[bool, str]:
    """Check Kafka connection."""
    try:
        from kafka import KafkaProducer
        from shared.config import get_settings
        
        settings = get_settings()
        producer = KafkaProducer(
            bootstrap_servers=settings.kafka.bootstrap_servers.split(","),
            client_id=settings.kafka.client_id,
        )
        producer.close()
        return True, "✓ Kafka connection successful"
    except Exception as e:
        return False, f"✗ Kafka connection failed: {e}"


def check_configuration() -> Tuple[bool, str]:
    """Check configuration loading."""
    try:
        from shared.config import get_settings
        
        settings = get_settings()
        assert settings.database.url
        assert settings.redis.url
        assert settings.kafka.bootstrap_servers
        assert settings.jwt.secret
        
        return True, "✓ Configuration loaded successfully"
    except Exception as e:
        return False, f"✗ Configuration error: {e}"


async def main():
    """Run all verification checks."""
    print("=" * 60)
    print("CloudScore ASTRA AI - Phase 1 Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Imports", check_imports),
        ("Configuration", check_configuration),
        ("Database", check_database),
        ("Redis", check_redis),
        ("Kafka", check_kafka),
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"Checking {name}...", end=" ")
        
        if asyncio.iscoroutinefunction(check_func):
            success, message = await check_func()
        else:
            success, message = check_func()
        
        print(message)
        results.append(success)
    
    print()
    print("=" * 60)
    
    if all(results):
        print("✓ All checks passed! Phase 1 setup is complete.")
        print()
        print("Next steps:")
        print("  1. Review the configuration in .env")
        print("  2. Explore the shared libraries in shared-libs/")
        print("  3. Check Temporal UI at http://localhost:8233")
        print("  4. Proceed to Phase 2 implementation")
        print()
        return 0
    else:
        print("✗ Some checks failed. Please review the errors above.")
        print()
        print("Troubleshooting:")
        print("  1. Ensure all Docker containers are running: docker-compose ps")
        print("  2. Check service logs: docker-compose logs -f")
        print("  3. Verify .env file exists and is configured")
        print("  4. Ensure shared libraries are installed: pip install -e shared-libs/")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
