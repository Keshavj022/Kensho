"""
Comprehensive test client for all agents
"""
import httpx
import asyncio
import json


BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


async def test_root():
    """Test root endpoint"""
    print("\n" + "="*60)
    print("Testing Root Endpoint")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(BASE_URL)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200


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


async def test_restaurant_recommendations():
    """Test restaurant recommendations"""
    print("\n" + "="*60)
    print("Testing Restaurant Recommendations")
    print("="*60)

    async with httpx.AsyncClient() as client:
        request_data = {
            "user_query": "I want healthy vegetarian lunch options",
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
            print(f"Recommendations: {len(result.get('recommendations', []))}")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_travel_itinerary():
    """Test travel itinerary creation"""
    print("\n" + "="*60)
    print("Testing Travel Itinerary Creation")
    print("="*60)

    async with httpx.AsyncClient() as client:
        request_data = {
            "destination": "Tokyo",
            "start_date": "2026-03-10",
            "end_date": "2026-03-17",
            "travelers": 2,
            "budget": 6000,
            "preferences": ["cultural", "dining"],
            "interests": ["sightseeing", "cultural", "dining"],
            "pace": "moderate",
            "include_flights": True,
            "include_hotels": True,
            "origin": "Los Angeles"
        }

        response = await client.post(
            f"{API_BASE}/travel/itinerary/create",
            json=request_data,
            timeout=60.0
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            itinerary = result.get("itinerary")
            if itinerary:
                print(f"\n✅ Itinerary Created Successfully!")
                print(f"   ID: {itinerary['id']}")
                print(f"   Destination: {itinerary['destination']}")
                print(f"   Duration: {itinerary['total_days']} days")
                print(f"   Total Cost: ${itinerary['total_cost']:.2f}")
                print(f"   Flights: {len(itinerary.get('flights', []))}")
                print(f"   Hotels: {len(itinerary.get('hotels', []))}")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_multi_agent_workflow():
    """Test combined workflow using both agents"""
    print("\n" + "="*60)
    print("Testing Multi-Agent Workflow")
    print("="*60)
    print("Scenario: Plan a trip and find restaurants at destination")

    async with httpx.AsyncClient() as client:
        # Step 1: Create travel itinerary
        print("\n1. Creating travel itinerary to Dubai...")
        itinerary_request = {
            "destination": "Dubai",
            "start_date": "2026-04-05",
            "end_date": "2026-04-10",
            "travelers": 2,
            "budget": 8000,
            "interests": ["adventure", "shopping"],
            "pace": "moderate",
            "include_flights": True,
            "include_hotels": True,
            "origin": "London"
        }

        itinerary_response = await client.post(
            f"{API_BASE}/travel/itinerary/create",
            json=itinerary_request,
            timeout=60.0
        )

        if itinerary_response.status_code != 200:
            print("❌ Failed to create itinerary")
            return False

        itinerary = itinerary_response.json().get("itinerary")
        print(f"✅ Itinerary created: {itinerary['id']}")

        # Step 2: Search for restaurants at destination
        print("\n2. Searching for restaurants in Dubai...")
        restaurant_search = {
            "query": "luxury dining",
            "location": "Dubai",
            "max_results": 5
        }

        restaurant_response = await client.post(
            f"{API_BASE}/search",
            json=restaurant_search,
            timeout=30.0
        )

        if restaurant_response.status_code == 200:
            restaurants = restaurant_response.json().get("results", [])
            print(f"✅ Found {len(restaurants)} restaurants")

            if restaurants:
                print(f"\nTop recommendation: {restaurants[0].get('name', 'N/A')}")

        # Step 3: Get activities at destination
        print("\n3. Getting activities in Dubai...")
        activities_response = await client.get(
            f"{API_BASE}/travel/activities/Dubai",
            timeout=30.0
        )

        if activities_response.status_code == 200:
            activities = activities_response.json().get("activities", [])
            print(f"✅ Found {len(activities)} activities")

        print("\n✅ Multi-Agent Workflow Completed!")
        return True


async def run_comprehensive_tests():
    """Run comprehensive test suite"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     Kensho Platform Test Suite                             ║
║     Testing Restaurant Agent + Travel Agent                ║
╚═══════════════════════════════════════════════════════════╝
    """)

    print("Ensure backend server is running at http://localhost:8000")
    print("\nStarting comprehensive tests in 3 seconds...")
    await asyncio.sleep(3)

    tests = [
        ("Root Endpoint", test_root),
        ("Health Check", test_health),
        ("Restaurant Recommendations", test_restaurant_recommendations),
        ("Travel Itinerary", test_travel_itinerary),
        ("Multi-Agent Workflow", test_multi_agent_workflow),
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
    print("Comprehensive Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")

    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 All tests passed! Both agents are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")


if __name__ == "__main__":
    try:
        asyncio.run(run_comprehensive_tests())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nError running tests: {str(e)}")
