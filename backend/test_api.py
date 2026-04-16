import requests
import json

investigation_id = 'b30b1e41-9605-47be-a0d1-cbeae04905cd'
url = f'http://localhost:8000/api/v1/investigations/{investigation_id}'

try:
    response = requests.get(url)
    data = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Status: {data.get('status')}")
    print(f"Agent Results: {len(data.get('agent_results', []))} agents")
    print(f"RCA: {'Yes' if data.get('rca') else 'No'}")
    print(f"Resolution: {'Yes' if data.get('resolution') else 'No'}")
    
    if data.get('agent_results'):
        print("\nAgent Details:")
        for agent in data['agent_results']:
            print(f"  - {agent.get('agent_type')}: success={agent.get('success')}, duration={agent.get('duration_seconds')}s, evidence={len(agent.get('evidence', []))}")
            
except Exception as e:
    print(f"Error: {e}")
