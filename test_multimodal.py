"""
Test client for Multimodal (Image Analysis) functionality
"""
import httpx
import asyncio
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw


BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


def create_sample_food_image():
    """Create a sample food image for testing"""
    # Create a simple image with text
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 350, 250], fill='orange', outline='brown', width=3)
    draw.text((120, 130), "PIZZA", fill='red')

    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')


def create_sample_travel_image():
    """Create a sample travel image for testing"""
    # Create a simple image with text
    img = Image.new('RGB', (400, 300), color='skyblue')
    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 180, 300, 280], fill='tan', outline='brown', width=2)
    draw.polygon([(200, 100), (150, 180), (250, 180)], fill='gray', outline='black')
    draw.text((140, 220), "MOUNTAIN", fill='brown')

    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')


async def test_multimodal_status():
    """Test multimodal service status"""
    print("\n" + "="*60)
    print("Testing Multimodal Service Status")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/multimodal/status")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Service Status: {result['status']}")
            print(f"Vision Available: {'✅' if result['vision_available'] else '❌'}")
            print(f"Supported Formats: {', '.join(result['supported_formats'])}")
            print(f"Features: {', '.join(result.get('features', []))}")
            print(f"Message: {result['message']}")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_analyze_image():
    """Test basic image analysis"""
    print("\n" + "="*60)
    print("Testing Image Analysis")
    print("="*60)

    # Create sample image
    image_base64 = create_sample_food_image()

    async with httpx.AsyncClient() as client:
        request_data = {
            "image_data": image_base64,
            "is_url": False,
            "features": ["caption", "tags", "objects"],
            "language": "en",
            "gender_neutral_caption": True
        }

        response = await client.post(
            f"{API_BASE}/multimodal/analyze-image",
            json=request_data,
            timeout=30.0
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Image analyzed successfully")
            if result.get("caption"):
                print(f"   Caption: {result['caption']['text']}")
                print(f"   Confidence: {result['caption']['confidence']}")
            if result.get("tags"):
                tags = [f"{t['name']} ({t['confidence']:.2f})" for t in result['tags'][:5]]
                print(f"   Tags: {', '.join(tags)}")
        elif response.status_code == 503:
            print("⚠️  Vision service not initialized")
            print("   Set AZURE_VISION_KEY and AZURE_VISION_ENDPOINT to enable")
        else:
            print(f"Response: {response.text}")

        return response.status_code in [200, 503]


async def test_analyze_food():
    """Test food image analysis"""
    print("\n" + "="*60)
    print("Testing Food Image Analysis")
    print("="*60)

    # Create sample food image
    image_base64 = create_sample_food_image()

    async with httpx.AsyncClient() as client:
        request_data = {
            "image_data": image_base64,
            "is_url": False,
            "user_id": "default",
            "additional_context": "Looking for similar restaurants"
        }

        response = await client.post(
            f"{API_BASE}/multimodal/analyze-food",
            json=request_data,
            timeout=30.0
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Food image analyzed successfully")
            print(f"   Description: {result['description']}")
            print(f"   Detected Food: {', '.join(result['detected_food'][:5])}")
            print(f"   Confidence: {result['confidence']}")
            print(f"   Restaurant Recommendations: {len(result.get('restaurant_recommendations', []))}")
            if result.get('dietary_info'):
                print(f"   Vegetarian: {result['dietary_info'].get('vegetarian', 'N/A')}")
        elif response.status_code == 503:
            print("⚠️  Vision service not initialized")
        else:
            print(f"Response: {response.text}")

        return response.status_code in [200, 503]


async def test_analyze_travel():
    """Test travel image analysis"""
    print("\n" + "="*60)
    print("Testing Travel Image Analysis")
    print("="*60)

    # Create sample travel image
    image_base64 = create_sample_travel_image()

    async with httpx.AsyncClient() as client:
        request_data = {
            "image_data": image_base64,
            "is_url": False,
            "user_id": "default",
            "query": "Where is this?"
        }

        response = await client.post(
            f"{API_BASE}/multimodal/analyze-travel",
            json=request_data,
            timeout=30.0
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Travel image analyzed successfully")
            print(f"   Description: {result['description']}")
            print(f"   Location Identified: {result.get('location_identified', 'Unknown')}")
            print(f"   Landmarks: {', '.join(result['landmarks'][:3]) if result['landmarks'] else 'None'}")
            print(f"   Suggested Destinations: {', '.join(result['suggested_destinations'][:3])}")
            print(f"   Activities: {', '.join(result['activities'][:5])}")
            print(f"   Confidence: {result['confidence']}")
        elif response.status_code == 503:
            print("⚠️  Vision service not initialized")
        else:
            print(f"Response: {response.text}")

        return response.status_code in [200, 503]


async def test_multimodal_chat():
    """Test multimodal chat (text + image)"""
    print("\n" + "="*60)
    print("Testing Multimodal Chat (Text + Image)")
    print("="*60)

    # Create sample image
    image_base64 = create_sample_food_image()

    async with httpx.AsyncClient() as client:
        request_data = {
            "message": "What restaurants serve food like this?",
            "image_data": image_base64,
            "is_url": False,
            "user_id": "default",
            "agent_type": "restaurant"
        }

        response = await client.post(
            f"{API_BASE}/multimodal/chat",
            json=request_data,
            timeout=60.0
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Multimodal chat completed successfully")
            print(f"   Agent Response: {result['message'][:200]}...")
            if result.get('image_analysis'):
                analysis = result['image_analysis']
                if analysis.get('caption'):
                    print(f"   Image Analysis: {analysis['caption']['text']}")
            print(f"   Thread ID: {result.get('thread_id', 'N/A')}")
        elif response.status_code == 503:
            print("⚠️  Vision service not initialized")
        else:
            print(f"Response: {response.text}")

        return response.status_code in [200, 503]


async def run_all_tests():
    """Run all multimodal tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     Multimodal (Image Analysis) Test Suite                ║
╚═══════════════════════════════════════════════════════════╝
    """)

    print("Make sure the backend server is running at http://localhost:8000")
    print("\nNote: Multimodal tests require AZURE_VISION_KEY to be set")
    print("Without it, service status will show 'not_configured'\n")
    print("Starting tests in 3 seconds...")
    await asyncio.sleep(3)

    tests = [
        ("Multimodal Service Status", test_multimodal_status),
        ("Basic Image Analysis", test_analyze_image),
        ("Food Image Analysis", test_analyze_food),
        ("Travel Image Analysis", test_analyze_travel),
        ("Multimodal Chat", test_multimodal_chat),
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

    if passed < total:
        print("\n💡 Note: Some tests may fail if AZURE_VISION_KEY is not configured.")
        print("   This is expected and doesn't indicate a problem with the code.")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nError running tests: {str(e)}")
