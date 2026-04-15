"""Add context column to chat_threads table."""
import sqlite3

def migrate():
    conn = sqlite3.connect('sre_agent.db')
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(chat_threads)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'context' not in columns:
            print("Adding context column to chat_threads table...")
            cursor.execute("ALTER TABLE chat_threads ADD COLUMN context TEXT")
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Context column already exists, skipping migration.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
