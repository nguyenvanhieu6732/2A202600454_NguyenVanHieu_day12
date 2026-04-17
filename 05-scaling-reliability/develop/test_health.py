import requests
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    print("Testing /health endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/health")
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        assert r.status_code == 200
        print("OK: Health check passed")
    except Exception as e:
        print(f"FAIL: Health check failed - {e}")

def test_ready():
    print("\nTesting /ready endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/ready")
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        assert r.status_code in [200, 503]
        if r.status_code == 200:
            print("OK: Agent is ready")
        else:
            print("INFO: Agent is not ready yet (normal during startup)")
    except Exception as e:
        print(f"FAIL: Readiness check failed - {e}")

if __name__ == "__main__":
    test_health()
    test_ready()
