import sqlite3

conn = sqlite3.connect('sre_agent.db')
cursor = conn.cursor()

# Check for investigations in progress
cursor.execute('''
    SELECT id, incident_number, status, started_at 
    FROM investigations 
    WHERE status IN ('investigating', 'started')
    ORDER BY started_at DESC 
    LIMIT 5
''')

rows = cursor.fetchall()
if rows:
    print("Investigations in progress:")
    for r in rows:
        print(f"  {r[0]}: {r[1]} - {r[2]} - {r[3]}")
else:
    print("No investigations in progress")

# Check most recent completed
cursor.execute('''
    SELECT id, incident_number, status, started_at 
    FROM investigations 
    WHERE status = 'rca_complete'
    ORDER BY started_at DESC 
    LIMIT 3
''')

rows = cursor.fetchall()
print("\nMost recent completed:")
for r in rows:
    print(f"  {r[0]}: {r[1]} - {r[2]} - {r[3]}")

conn.close()
