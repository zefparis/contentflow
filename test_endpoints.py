import requests
import json

def test_endpoint(method, path, data=None):
    url = f"http://localhost:8000{path}"
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json=data)
        
        print(f"{method.upper()} {path} -> {response.status_code}")
        if response.status_code >= 400:
            print(f"  Error: {response.text}")
        else:
            try:
                print(f"  Response: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"  Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"{method.upper()} {path} -> Error: {str(e)}")
        return False

def run_tests():
    print("\n=== Testing Stub Endpoints ===")
    test_endpoint("GET", "/api/assets")
    test_endpoint("GET", "/api/posts")
    test_endpoint("GET", "/api/sources")
    test_endpoint("GET", "/api/jobs/status")
    test_endpoint("GET", "/api/payments/calculate")

    print("\n=== Testing BYOP Endpoints ===")
    test_endpoint("GET", "/api/byop/config")
    test_endpoint("GET", "/api/byop/submissions")

    print("\n=== Testing Magic Link Endpoints ===")
    test_email = "test@example.com"
    for path in [
        "/api/partner/auth/magic-link",
        "/api/auth/magic-link"
    ]:
        print(f"\nTesting {path}")
        test_endpoint("POST", path, {"email": test_email})

if __name__ == "__main__":
    run_tests()
