"""
Quick start script for Kensho backend
"""
import subprocess
import sys
import os
from pathlib import Path


def check_virtual_env():
    """Check if virtual environment is activated"""
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )


def main():
    """Run the backend server"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     Kensho Backend                                         ║
║     Starting server...                                    ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Check if virtual environment is activated
    if not check_virtual_env():
        print("⚠️  Virtual environment is not activated!")
        print("\nPlease activate the virtual environment first:")
        print("  Linux/Mac: source venv/bin/activate")
        print("  Windows:   venv\\Scripts\\activate")
        print("\nThen run this script again.")
        sys.exit(1)

    # Check if .env file exists
    env_file = Path("backend/.env")
    if not env_file.exists():
        print("⚠️  .env file not found!")
        print("\nPlease create backend/.env file with your Azure credentials.")
        print("You can copy backend/.env.example as a template.")
        print("\nThe server will start in local mode without Azure AI integration.")
        input("\nPress Enter to continue anyway or Ctrl+C to exit...")

    # Check if data files exist
    data_dir = Path("backend/data")
    if not (data_dir / "user_data.json").exists():
        print("⚠️  backend/data/user_data.json not found!")
        print("Please ensure user data file exists.")
        sys.exit(1)

    if not (data_dir / "restaurant_data.json").exists():
        print("⚠️  backend/data/restaurant_data.json not found!")
        print("Please ensure restaurant data file exists.")
        sys.exit(1)

    # Start the server
    print("\n🚀 Starting FastAPI server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")

    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
