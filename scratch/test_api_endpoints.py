import requests

def main():
    base_url = "http://localhost:8000"
    login_url = f"{base_url}/api/v1/auth/login"
    exams_url = f"{base_url}/api/v1/examinations/"
    
    print("--- Attempting Admin Login ---")
    login_data = {
        "username": "admin",
        "password": "Admin123!"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"Login Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Login Failed! Error: {response.text}")
            return
            
        token = response.json().get("access_token")
        print("Login Successful! Received token.")
        
        print("\n--- Fetching Examinations ---")
        headers = {
            "Authorization": f"Bearer {token}"
        }
        res = requests.get(exams_url, headers=headers)
        print(f"GET /api/v1/examinations/ Status: {res.status_code}")
        print(f"Response data:")
        import json
        try:
            print(json.dumps(res.json(), indent=2))
        except Exception:
            print(res.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    main()
