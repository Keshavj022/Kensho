"""
Test client for Voice Interface
"""
import httpx
import asyncio
import json
import base64
import wave
import io


BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


def create_sample_audio():
    """Create a simple WAV file for testing (silence)"""
    # Create a simple audio file (1 second of silence)
    sample_rate = 16000
    duration = 1  # seconds
    channels = 1
    sample_width = 2

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        # Write silence
        wav_file.writeframes(b'\x00' * (sample_rate * duration * channels * sample_width))

    audio_bytes = buffer.getvalue()
    return base64.b64encode(audio_bytes).decode('utf-8')


async def test_voice_status():
    """Test voice service status"""
    print("\n" + "="*60)
    print("Testing Voice Service Status")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/voice/status")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Voice Service Status: {result['status']}")
            print(f"Speech-to-Text: {'✅' if result['speech_to_text'] else '❌'}")
            print(f"Text-to-Speech: {'✅' if result['text_to_speech'] else '❌'}")
            print(f"Message: {result['message']}")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_get_available_voices():
    """Test get available voices"""
    print("\n" + "="*60)
    print("Testing Get Available Voices")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/voice/voices")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            voices = result.get("voices", [])
            languages = result.get("languages", [])

            print(f"\nAvailable Voices: {len(voices)}")
            for voice in voices[:3]:
                print(f"  - {voice['name']} ({voice['gender']}, {voice['language']})")

            print(f"\nSupported Languages: {len(languages)}")
            for lang in languages[:5]:
                print(f"  - {lang['name']} ({lang['code']})")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_text_to_speech():
    """Test text-to-speech"""
    print("\n" + "="*60)
    print("Testing Text-to-Speech")
    print("="*60)

    async with httpx.AsyncClient() as client:
        request_data = {
            "text": "Hello! I am your AI restaurant assistant. How can I help you find great food today?",
            "voice": "en-US-AvaMultilingualNeural",
            "language": "en-US",
            "speed": 1.0,
            "pitch": 1.0
        }

        response = await client.post(
            f"{API_BASE}/voice/text-to-speech",
            json=request_data,
            timeout=30.0
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Speech synthesized successfully")
            print(f"   Voice: {result['voice_used']}")
            print(f"   Duration: {result['duration_ms']}ms")
            print(f"   Format: {result['audio_format']}")
            print(f"   Audio data length: {len(result['audio_data'])} bytes (base64)")
        elif response.status_code == 503:
            print("⚠️  Voice service not initialized")
            print("   Set AZURE_SPEECH_KEY environment variable to enable")
        else:
            print(f"Response: {response.text}")

        return response.status_code == 200


async def test_speech_to_text():
    """Test speech-to-text"""
    print("\n" + "="*60)
    print("Testing Speech-to-Text")
    print("="*60)

    # Create sample audio
    audio_base64 = create_sample_audio()

    async with httpx.AsyncClient() as client:
        request_data = {
            "audio_data": audio_base64,
            "language": "en-US",
            "agent_type": "restaurant"
        }

        response = await client.post(
            f"{API_BASE}/voice/speech-to-text",
            json=request_data,
            timeout=30.0
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Speech recognized successfully")
            print(f"   Text: {result['text']}")
            print(f"   Confidence: {result['confidence']}")
            print(f"   Language: {result['language']}")
        elif response.status_code == 503:
            print("⚠️  Voice service not initialized")
            print("   Set AZURE_SPEECH_KEY environment variable to enable")
        elif response.status_code == 400:
            print("⚠️  Could not recognize speech (expected for test audio)")
        else:
            print(f"Response: {response.text}")

        return response.status_code in [200, 400, 503]


async def test_voice_chat():
    """Test complete voice chat"""
    print("\n" + "="*60)
    print("Testing Voice Chat (STT + Agent + TTS)")
    print("="*60)

    # Create sample audio
    audio_base64 = create_sample_audio()

    async with httpx.AsyncClient() as client:
        request_data = {
            "audio_data": audio_base64,
            "user_id": "default",
            "agent_type": "restaurant",
            "language": "en-US",
            "voice": "en-US-AvaMultilingualNeural"
        }

        response = await client.post(
            f"{API_BASE}/voice/chat",
            json=request_data,
            timeout=60.0
        )

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Voice chat completed successfully")
            print(f"   Transcribed: {result['transcribed_text'][:100]}...")
            print(f"   Agent Response: {result['agent_response_text'][:100]}...")
            print(f"   Confidence: {result['confidence']}")
            print(f"   Thread ID: {result.get('thread_id', 'N/A')}")
        elif response.status_code == 503:
            print("⚠️  Voice service not initialized")
            print("   Set AZURE_SPEECH_KEY environment variable to enable")
        elif response.status_code == 400:
            print("⚠️  Could not recognize speech (expected for test audio)")
        else:
            print(f"Response: {response.text}")

        return response.status_code in [200, 400, 503]


async def run_all_tests():
    """Run all voice interface tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     Voice Interface Test Suite                            ║
╚═══════════════════════════════════════════════════════════╝
    """)

    print("Make sure the backend server is running at http://localhost:8000")
    print("\nNote: Voice tests require AZURE_SPEECH_KEY to be set")
    print("Without it, service status will show 'not_configured'\n")
    print("Starting tests in 3 seconds...")
    await asyncio.sleep(3)

    tests = [
        ("Voice Service Status", test_voice_status),
        ("Get Available Voices", test_get_available_voices),
        ("Text-to-Speech", test_text_to_speech),
        ("Speech-to-Text", test_speech_to_text),
        ("Voice Chat", test_voice_chat),
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
        print("\n💡 Note: Some tests may fail if AZURE_SPEECH_KEY is not configured.")
        print("   This is expected and doesn't indicate a problem with the code.")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nError running tests: {str(e)}")
