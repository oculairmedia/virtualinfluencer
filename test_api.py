import requests
import json

BASE_URL = "http://192.168.50.90:8000"

def test_health():
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_list_accounts():
    print("\n=== Testing List Accounts Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/accounts")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_session_status(account="quecreate"):
    print(f"\n=== Testing Session Status for {account} ===")
    try:
        response = requests.get(f"{BASE_URL}/session_status/{account}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_start_session(account="quecreate"):
    print(f"\n=== Testing Start Session for {account} ===")
    try:
        data = {
            "account": account,
            "config": None  # Use existing config
        }
        response = requests.post(f"{BASE_URL}/start_session", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_stop_session(account="quecreate"):
    print(f"\n=== Testing Stop Session for {account} ===")
    try:
        data = {
            "account": account
        }
        response = requests.post(f"{BASE_URL}/stop_session", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Test all endpoints
    test_health()
    test_list_accounts()
    test_session_status()
    test_start_session()  # Added this line
    
    # Wait a bit and check status again
    import time
    time.sleep(2)
    test_session_status()
