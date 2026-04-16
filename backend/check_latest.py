import sqlite3
import json

conn = sqlite3.connect('sre_agent.db')
cursor = conn.cursor()

investigation_id = 'b30b1e41-9605-47be-a0d1-cbeae04905cd'

cursor.execute('SELECT status, agent_results, rca, resolution FROM investigations WHERE id = ?', (investigation_id,))
row = cursor.fetchone()

if row:
    status, agent_results_json, rca_json, resolution_json = row
    print(f"Status: {status}")
    
    if agent_results_json:
        agent_results = json.loads(agent_results_json)
        print(f"Agent Results: {len(agent_results)} agents")
        for agent in agent_results:
            print(f"  - {agent.get('agent_type')}: {agent.get('success')}, duration={agent.get('duration_seconds')}s")
    else:
        print("No agent results")
    
    print(f"\nRCA: {'Yes' if rca_json else 'No'}")
    print(f"Resolution: {'Yes' if resolution_json else 'No'}")
else:
    print("Investigation not found")

conn.close()
