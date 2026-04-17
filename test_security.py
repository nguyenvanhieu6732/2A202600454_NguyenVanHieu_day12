import requests
import time
import os

BASE_URL = "http://localhost:8000"

def detect_mode():
    """Tự động nhận diện bản develop (API Key) hay production (JWT)"""
    print("Detecting API mode...")
    try:
        # Thử gọi endpoint /auth/token
        r = requests.post(f"{BASE_URL}/auth/token", json={})
        if r.status_code != 404:
            print("Mode detected: PRODUCTION (JWT Authentication)")
            return "production"
    except:
        pass
    
    print("Mode detected: DEVELOP (API Key Authentication)")
    return "develop"

# --- PRODUCTION MODE LOGIC ---
def get_jwt_token(username, password):
    r = requests.post(
        f"{BASE_URL}/auth/token",
        json={"username": username, "password": password}
    )
    if r.status_code == 200:
        return r.json()["access_token"]
    return None

def test_production():
    print("\n[Test 1] Testing JWT Authentication...")
    # 1. No token
    r = requests.post(f"{BASE_URL}/ask", json={"question": "hello"})
    assert r.status_code == 401
    print("OK: Rejected access without token")
    
    # 2. Valid token
    token = get_jwt_token("student", "demo123")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE_URL}/ask", headers=headers, json={"question": "hello"})
    assert r.status_code == 200
    print("OK: Accepted valid token")

    print("\n[Test 2] Testing Rate Limiting...")
    for i in range(12):
        r = requests.post(f"{BASE_URL}/ask", headers=headers, json={"question": f"req {i}"})
        if r.status_code == 429:
            print(f"OK: Rate limited successfully at request {i+1}")
            break
    else:
        print("FAIL: Rate limit failed to trigger")

# --- DEVELOP MODE LOGIC ---
def test_develop():
    API_KEY = "demo-key-change-in-production" # Default in develop/app.py
    print("\n[Test 1] Testing API Key Authentication...")
    
    # 1. No key
    r = requests.post(f"{BASE_URL}/ask", json={"question": "hello"})
    assert r.status_code == 401
    print("OK: Rejected access without API Key")
    
    # 2. Invalid key
    r = requests.post(f"{BASE_URL}/ask", headers={"X-API-Key": "wrong-key"}, json={"question": "hello"})
    assert r.status_code == 403
    print("OK: Rejected invalid API Key")
    
    # 3. Valid key
    r = requests.post(f"{BASE_URL}/ask", headers={"X-API-Key": API_KEY}, json={"question": "hello"})
    if r.status_code != 200:
        # Thử lại với query param
        r = requests.post(f"{BASE_URL}/ask?question=hello", headers={"X-API-Key": API_KEY})
        
    assert r.status_code == 200
    print("OK: Accepted valid API Key")

if __name__ == "__main__":
    mode = detect_mode()
    try:
        if mode == "production":
            test_production()
        else:
            test_develop()
        print("\nAll security tests passed for this mode!")
    except AssertionError as e:
        print(f"\nFAIL: Assertion failed: {e}")
    except Exception as e:
        print(f"\nERROR: Error during test: {e}")