"""Script to add related_knowledge column to investigations table."""
import sqlite3

# Connect to database
conn = sqlite3.connect('sre_agent.db')
cursor = conn.cursor()

try:
    # Check if column exists
    cursor.execute("PRAGMA table_info(investigations)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'related_knowledge' not in columns:
        print("Adding related_knowledge column to investigations table...")
        cursor.execute("ALTER TABLE investigations ADD COLUMN related_knowledge TEXT")
        conn.commit()
        print("✓ Column added successfully")
    else:
        print("✓ Column already exists")
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
