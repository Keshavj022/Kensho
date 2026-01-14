"""
Setup script for Kensho Backend
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command with error handling"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        print(f"✅ {description} - Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed!")
        print(f"Error: {e.stderr}")
        return False


def setup_backend():
    """Set up the backend environment"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║     Kensho Backend Setup                                   ║
║     Restaurant Agent + Travel Agent                       ║
║     Powered by Azure AI Foundry                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Check Python version
    print(f"🐍 Python Version: {sys.version}")
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required!")
        sys.exit(1)

    # Create virtual environment
    venv_path = Path("venv")
    if not venv_path.exists():
        if not run_command(
            f"{sys.executable} -m venv venv",
            "Creating virtual environment"
        ):
            sys.exit(1)
    else:
        print("\n✓ Virtual environment already exists")

    # Determine pip command
    if sys.platform == "win32":
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"

    # Upgrade pip
    run_command(
        f"{pip_cmd} install --upgrade pip",
        "Upgrading pip"
    )

    # Install dependencies
    if not run_command(
        f"{pip_cmd} install -r backend/requirements.txt",
        "Installing dependencies"
    ):
        sys.exit(1)

    # Create .env file if it doesn't exist
    env_file = Path("backend/.env")
    env_template = Path("backend/.env.template")

    if not env_file.exists():
        if env_template.exists():
            print("\n📝 Creating .env file from template...")
            with open(env_template, "r") as src, open(env_file, "w") as dst:
                dst.write(src.read())
            print("✅ .env file created. Please update it with your Azure credentials.")
        else:
            print("\n⚠️  .env.template not found!")
    else:
        print("\n✓ .env file already exists")

    # Check data files
    data_dir = Path("backend/data")
    if data_dir.exists():
        data_files = [
            "user_data.json",
            "restaurant_data.json",
            "flights_data.json",
            "hotels_data.json",
            "destinations_data.json"
        ]

        print("\n📁 Checking data files:")
        for file_name in data_files:
            file_path = data_dir / file_name
            if file_path.exists():
                print(f"✓ {file_name}")
            else:
                print(f"⚠️  {file_name} - Missing")

    print(f"""
╔═══════════════════════════════════════════════════════════╗
║     Setup Complete!                                        ║
╚═══════════════════════════════════════════════════════════╝

Next Steps:
1. Configure your Azure AI Foundry credentials in backend/.env
   (Optional - system works in local mode without Azure)

2. Activate the virtual environment:
   - Linux/Mac: source venv/bin/activate
   - Windows: venv\\Scripts\\activate

3. Run the backend server:
   python run_backend.py
   OR
   python -m backend.main

4. Access the API documentation:
   http://localhost:8000/docs

5. Test the agents:
   python test_all_agents.py (All agents)
   python test_client.py (Restaurant agent)
   python test_travel_agent.py (Travel agent)

Available Agents:
- Restaurant Agent: Personalized food recommendations with RAG
- Travel Agent: Itinerary planning with flights, hotels, and activities
    """)


if __name__ == "__main__":
    setup_backend()
