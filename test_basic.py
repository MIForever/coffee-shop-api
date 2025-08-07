import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health_check():
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health/")
        print(f"Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Failed: {e}")
        return False

def test_user_registration():
    print("Testing user registration...")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_data = {
            "email": f"test_{timestamp}@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=user_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            return True
        else:
            print(f"Error: {response.json()}")
            return False
    except Exception as e:
        print(f"Failed: {e}")
        return False

def test_user_login():
    print("Testing user login...")
    try:
        login_data = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            tokens = response.json()
            print("Login successful")
            return tokens
        else:
            print(f"Failed: {response.json()}")
            return None
    except Exception as e:
        print(f"Failed: {e}")
        return None

def test_me_endpoint(tokens):
    if not tokens:
        print("No tokens for /me test")
        return False
    
    print("Testing /me endpoint...")
    try:
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        response = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"User: {user_data['email']}")
            return True
        else:
            print(f"Failed: {response.json()}")
            return False
    except Exception as e:
        print(f"Failed: {e}")
        return False

def test_docs():
    print("Testing API documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Failed: {e}")
        return False

def main():
    print("Coffee Shop API - Basic Test")
    print("=" * 30)
    
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health_check),
        ("User Registration", test_user_registration),
        ("API Documentation", test_docs),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
    
    print("\n--- Authentication Tests ---")
    print("Note: Login requires email verification")
    results.append(("User Login", "SKIP"))
    results.append(("/me Endpoint", "SKIP"))
    
    print("\n--- Test Summary ---")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        if result == "SKIP":
            status = "SKIP"
            print(f"{test_name}: {status}")
        else:
            status = "PASS" if result else "FAIL"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed!")
    else:
        print("Some tests failed.")

if __name__ == "__main__":
    main()
