import sqlite3
import json

conn = sqlite3.connect('sre_agent.db')
cursor = conn.cursor()

investigation_id = '3fc76e72-4dea-4158-8d42-1b77b071b93a'

cursor.execute('SELECT agent_results FROM investigations WHERE id = ?', (investigation_id,))
row = cursor.fetchone()

if row and row[0]:
    agent_results = json.loads(row[0])
    print(f"Agent results count: {len(agent_results)}")
    for agent in agent_results:
        print(f"  - {agent.get('agent_type')}: {agent.get('success')}")
else:
    print("No agent results")

conn.close()
