"""Add service_name column to investigations table."""

import sqlite3
import sys
from pathlib import Path

def migrate():
    """Add service_name column to investigations table."""
    db_path = Path(__file__).parent / "sre_agent.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(investigations)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "service_name" in columns:
            print("Column 'service_name' already exists in investigations table")
        else:
            # Add the column
            cursor.execute("ALTER TABLE investigations ADD COLUMN service_name VARCHAR(255)")
            conn.commit()
            print("Successfully added 'service_name' column to investigations table")
    
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
