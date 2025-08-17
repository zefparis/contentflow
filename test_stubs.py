import httpx
import asyncio

BASE_URL = "http://localhost:8000"  # Update if your server runs on a different port

async def test_endpoint(method, path, json=None):
    url = f"{BASE_URL}{path}"
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url)
            else:
                response = await client.post(url, json=json)
            
            print(f"{method.upper()} {path} -> {response.status_code}")
            if response.status_code >= 400:
                print(f"  Error: {response.text}")
            else:
                print(f"  Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"{method.upper()} {path} -> Error: {str(e)}")
            return False

async def run_tests():
    print("\n=== Testing Stub Endpoints ===")
    await test_endpoint("GET", "/api/assets")
    await test_endpoint("GET", "/api/posts")
    await test_endpoint("GET", "/api/sources")
    await test_endpoint("GET", "/api/jobs/status")
    await test_endpoint("GET", "/api/payments/calculate")

    print("\n=== Testing BYOP Endpoints ===")
    await test_endpoint("GET", "/api/byop/config")
    await test_endpoint("GET", "/api/byop/submissions")

    print("\n=== Testing Magic Link Endpoints ===")
    # Test both magic link endpoints
    test_email = "test@example.com"
    for path in [
        "/api/partner/auth/magic-link",
        "/api/auth/magic-link"  # Alias
    ]:
        print(f"\nTesting {path}")
        await test_endpoint("POST", path, json={"email": test_email})

if __name__ == "__main__":
    asyncio.run(run_tests())
