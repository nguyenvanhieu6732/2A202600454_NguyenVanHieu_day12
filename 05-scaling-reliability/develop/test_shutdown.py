import requests
import threading
import time
import os
import signal
import subprocess
import sys

BASE_URL = "http://localhost:8000"

def send_long_request():
    print("[Client] Sending long request (5s delay)...")
    try:
        # Sử dụng query param 'delay' mà ta vừa thêm vào app.py
        r = requests.post(f"{BASE_URL}/ask?question=ping&delay=5", timeout=10)
        print(f"[Client] Response received: {r.status_code} - {r.json()}")
    except Exception as e:
        print(f"[Client] Request failed: {e}")

def run_test():
    print("=== Graceful Shutdown Test ===")
    
    # 1. Start long request in background
    thread = threading.Thread(target=send_long_request)
    thread.start()
    
    # 2. Wait a bit for the request to be 'in-flight'
    time.sleep(1)
    
    # 3. Prompt user to kill the server or try to do it automatically
    print("\n[Test] NOW: Please go to the server terminal and press CTRL+C")
    print("[Test] Or, if you are running this from a script, the server should handle SIGTERM.")
    print("[Test] Waiting for the request thread to finish...")
    
    thread.join()
    print("\n[Test] Conclusion: If the response above is 200, Graceful Shutdown WORKED!")
    print("[Test] If the request failed with ConnectionError, Graceful Shutdown FAILED.")

if __name__ == "__main__":
    run_test()
