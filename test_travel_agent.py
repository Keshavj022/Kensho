"""
Test client for the Travel Agent API
"""
import httpx
import asyncio
import json
from datetime import datetime, timedelta


BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


async def test_search_flights():
    """Test flight search"""
    print("\n" + "="*60)
    print("Testing Flight Search")
    print("="*60)

    async with httpx.AsyncClient() as client:
        request_data = {
            "origin": "New York",
            "destination": "Paris",
            "departure_date": "2026-02-15",
            "return_date": "2026-02-22",
            "passengers": 2,
            "travel_class": "economy",
            "trip_type": "round_trip"
        }

        response = await client.post(
            f"{API_BASE}/travel/flights/search",
            json=request_data,
            timeout=30.0
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            flights = result.get("flights", [])
            print(f"\nFound {len(flights)} flights")

            for i, flight in enumerate(flights[:2], 1):
                print(f"\nFlight {i}:")
                print(f"  Airline: {flight['airline']}")
                print(f"  Route: {flight['origin']} -> {flight['destination']}")
                print(f"  Price: ${flight['price']}")
                print(f"  Duration: {flight['total_duration']}")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_search_hotels():
    """Test hotel search"""
    print("\n" + "="*60)
    print("Testing Hotel Search")
    print("="*60)

    async with httpx.AsyncClient() as client:
        request_data = {
            "location": "Paris",
            "check_in": "2026-02-15",
            "check_out": "2026-02-22",
            "guests": 2,
            "rooms": 1,
            "min_rating": 4.0
        }

        response = await client.post(
            f"{API_BASE}/travel/hotels/search",
            json=request_data,
            timeout=30.0
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            hotels = result.get("hotels", [])
            print(f"\nFound {len(hotels)} hotels")

            for i, hotel in enumerate(hotels[:2], 1):
                print(f"\nHotel {i}:")
                print(f"  Name: {hotel['name']}")
                print(f"  Rating: {hotel['rating']} stars")
                print(f"  Price: ${hotel['price_per_night']}/night")
                print(f"  Total: ${hotel.get('total_price', 'N/A')}")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_get_destinations():
    """Test get destinations"""
    print("\n" + "="*60)
    print("Testing Get Destinations")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/travel/destinations")

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            destinations = result.get("destinations", [])
            print(f"\nFound {len(destinations)} destinations")
            print(f"Destinations: {', '.join(destinations)}")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_get_destination_info():
    """Test get destination info"""
    print("\n" + "="*60)
    print("Testing Get Destination Info")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/travel/destinations/Paris")

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            info = response.json()
            print(f"\nDestination: {info['name']}, {info['country']}")
            print(f"Description: {info['description']}")
            print(f"Best time to visit: {info['best_time_to_visit']}")
            print(f"Activities available: {len(info.get('activities', []))}")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_get_activities():
    """Test get activities"""
    print("\n" + "="*60)
    print("Testing Get Activities")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/travel/activities/Paris")

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            activities = result.get("activities", [])
            print(f"\nFound {len(activities)} activities")

            for i, activity in enumerate(activities[:3], 1):
                print(f"\n{i}. {activity['name']}")
                print(f"   Type: {activity['type']}")
                print(f"   Duration: {activity['duration']}")
                print(f"   Price: ${activity['price']}")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_create_itinerary():
    """Test create itinerary"""
    print("\n" + "="*60)
    print("Testing Create Itinerary")
    print("="*60)

    # Calculate dates
    start_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        request_data = {
            "destination": "Paris",
            "start_date": start_date,
            "end_date": end_date,
            "travelers": 2,
            "budget": 5000,
            "preferences": ["cultural", "dining"],
            "interests": ["sightseeing", "cultural", "dining"],
            "pace": "moderate",
            "include_flights": True,
            "include_hotels": True,
            "origin": "New York"
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
                print(f"\nItinerary Created:")
                print(f"  ID: {itinerary['id']}")
                print(f"  Destination: {itinerary['destination']}")
                print(f"  Duration: {itinerary['total_days']} days")
                print(f"  Total Cost: ${itinerary['total_cost']:.2f}")
                print(f"  Flights: {len(itinerary.get('flights', []))}")
                print(f"  Hotels: {len(itinerary.get('hotels', []))}")
                print(f"  Daily Plans: {len(itinerary.get('daily_itinerary', []))}")

                # Show first day
                if itinerary.get('daily_itinerary'):
                    day1 = itinerary['daily_itinerary'][0]
                    print(f"\n  Day 1 ({day1['date']}):")
                    print(f"    Location: {day1['location']}")
                    print(f"    Activities: {len(day1.get('activities', []))}")
                    for act in day1.get('activities', [])[:2]:
                        print(f"      - {act['name']} ({act.get('time_slot', 'TBD')})")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_travel_chat():
    """Test travel chat"""
    print("\n" + "="*60)
    print("Testing Travel Chat")
    print("="*60)

    async with httpx.AsyncClient() as client:
        request_data = {
            "message": "I want to plan a romantic trip to Paris for 7 days. What do you recommend?",
            "user_id": "default"
        }

        response = await client.post(
            f"{API_BASE}/travel/chat",
            json=request_data,
            timeout=30.0
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"\nAgent Response:")
            print(result.get('message'))
            print(f"\nThread ID: {result.get('thread_id')}")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def run_all_tests():
    """Run all travel agent tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     Travel Agent API Test Suite                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    print("Make sure the backend server is running at http://localhost:8000")
    print("\nStarting tests in 3 seconds...")
    await asyncio.sleep(3)

    tests = [
        ("Get Destinations", test_get_destinations),
        ("Get Destination Info", test_get_destination_info),
        ("Get Activities", test_get_activities),
        ("Search Flights", test_search_flights),
        ("Search Hotels", test_search_hotels),
        ("Create Itinerary", test_create_itinerary),
        ("Travel Chat", test_travel_chat),
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
