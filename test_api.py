import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"

def test_health():
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_list_accounts():
    print("\n=== Testing List Accounts Endpoint ===")
    response = requests.get(f"{BASE_URL}/accounts")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.json()}")

def test_session_status(account):
    print(f"\n=== Testing Session Status for {account} ===")
    response = requests.get(f"{BASE_URL}/sessions/status/{account}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_start_session(account):
    print(f"\n=== Testing Start Session for {account} ===")
    response = requests.post(f"{BASE_URL}/sessions/start_session", json={"account": account})
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    test_health()
    test_list_accounts()
    test_session_status("quecreate")
    test_start_session("quecreate")
    test_session_status("quecreate")
