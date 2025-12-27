import requests
from app import app

# Simulate logged in user
client = app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 2 # Assuming ID 2 is Company User (from seed)
    sess['role'] = 'Company User'
    sess['user_name'] = 'Test User'

# Test 1: List all
print("--- List All ---")
res = client.get('/api/equipment')
if res.status_code == 200:
    print(f"Count: {len(res.json)}")
else:
    print(f"Error: {res.status_code} {res.data}")

# Test 2: Search for 'lathe' (assuming seed data)
print("\n--- Search 'Machine' ---")
res = client.get('/api/equipment?search=Machine')
if res.status_code == 200:
    print(f"Count: {len(res.json)}")
    for item in res.json:
        print(f" - {item['name']} ({item['serial_number']})")
else:
    print(f"Error: {res.status_code} {res.data}")
