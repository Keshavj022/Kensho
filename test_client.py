"""
Test client for Kensho Restaurant Agent API
"""
import httpx
import asyncio
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


async def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200


async def test_agent_status():
    """Test agent status endpoint"""
    print("\n" + "="*60)
    print("Testing Agent Status Endpoint")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/agent/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200


async def test_get_user():
    """Test get user endpoint"""
    print("\n" + "="*60)
    print("Testing Get User Endpoint")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/user/default")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"User: {user_data['profile']['name']}")
            print(f"Location: {user_data['profile']['location']}")
            print(f"Dietary Type: {user_data['dietary']['type']}")
        else:
            print(f"Response: {response.text}")
        return response.status_code == 200


async def test_search_restaurants():
    """Test restaurant search endpoint"""
    print("\n" + "="*60)
    print("Testing Restaurant Search Endpoint")
    print("="*60)

    async with httpx.AsyncClient() as client:
        search_query = {
            "query": "pizza",
            "max_results": 5
        }
        response = await client.post(f"{API_BASE}/search", json=search_query)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"Found {results['count']} restaurants")
            for i, restaurant in enumerate(results['results'][:3], 1):
                print(f"\n{i}. {restaurant.get('name', 'N/A')}")
                print(f"   Cuisine: {restaurant.get('cuisine', 'N/A')}")
                print(f"   Location: {restaurant.get('location', 'N/A')}")
        else:
            print(f"Response: {response.text}")
        return response.status_code == 200


async def test_recommendations():
    """Test recommendations endpoint"""
    print("\n" + "="*60)
    print("Testing Recommendations Endpoint")
    print("="*60)

    async with httpx.AsyncClient() as client:
        request_data = {
            "user_query": "I want healthy vegetarian food",
            "user_id": "default"
        }
        response = await client.post(
            f"{API_BASE}/recommendations",
            json=request_data,
            timeout=30.0
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"\nExplanation: {result.get('explanation', 'N/A')}")
            recommendations = result.get('recommendations', [])
            print(f"\nFound {len(recommendations)} recommendations")
            for i, restaurant in enumerate(recommendations[:3], 1):
                print(f"\n{i}. {restaurant.get('name', 'N/A')}")
        else:
            print(f"Response: {response.text}")
        return response.status_code == 200


async def test_chat():
    """Test chat endpoint"""
    print("\n" + "="*60)
    print("Testing Chat Endpoint")
    print("="*60)

    async with httpx.AsyncClient() as client:
        request_data = {
            "message": "Can you recommend some Italian restaurants?",
            "user_id": "default"
        }
        response = await client.post(
            f"{API_BASE}/chat",
            json=request_data,
            timeout=30.0
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"\nAgent Response:")
            print(result.get('message', 'N/A'))
            print(f"\nThread ID: {result.get('thread_id', 'N/A')}")
        else:
            print(f"Response: {response.text}")
        return response.status_code == 200


async def test_get_cuisines():
    """Test get cuisines endpoint"""
    print("\n" + "="*60)
    print("Testing Get Cuisines Endpoint")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/cuisines")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            cuisines = result.get('cuisines', [])
            print(f"Found {len(cuisines)} cuisines")
            print(f"Cuisines: {', '.join(cuisines[:10])}")
        else:
            print(f"Response: {response.text}")
        return response.status_code == 200


async def run_all_tests():
    """Run all tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     Kensho Restaurant Agent API Test Suite                 ║
╚═══════════════════════════════════════════════════════════╝
    """)

    print("Make sure the backend server is running at http://localhost:8000")
    print("You can start it with: python run_backend.py")
    print("\nStarting tests in 3 seconds...")
    await asyncio.sleep(3)

    tests = [
        ("Health Check", test_health),
        ("Agent Status", test_agent_status),
        ("Get User", test_get_user),
        ("Get Cuisines", test_get_cuisines),
        ("Search Restaurants", test_search_restaurants),
        ("Recommendations", test_recommendations),
        ("Chat", test_chat),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error in {test_name}: {str(e)}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")

    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nError running tests: {str(e)}")
