"""
Script to clean all incidents from Astra DB
"""
import asyncio
from sqlalchemy import text
from app.db.base import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


async def clean_all_incidents():
    """Delete all incidents from the database."""
    async with AsyncSessionLocal() as db:
        try:
            # Delete all incidents
            result = await db.execute(text("DELETE FROM incidents"))
            await db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} incidents from database")
            print(f"✓ Successfully deleted {deleted_count} incidents from Astra DB")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to clean incidents: {str(e)}")
            print(f"✗ Failed to clean incidents: {str(e)}")
            raise


if __name__ == "__main__":
    print("Cleaning all incidents from Astra DB...")
    asyncio.run(clean_all_incidents())
