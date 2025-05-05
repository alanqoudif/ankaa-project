#!/bin/bash
# Setup script for Ankaa Project (ShariaAI - Omani Legal Assistant)
# This script automates the installation process and handles common issues

echo "Setting up Ankaa Project (ShariaAI - Omani Legal Assistant)..."
echo "=============================================================="

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS system"
    echo "Checking if Homebrew is installed..."
    
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "Homebrew is already installed."
    fi
    
    echo "Installing PortAudio (required for PyAudio)..."
    brew install portaudio
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected Linux system"
    echo "Installing required system dependencies..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y python3-dev portaudio19-dev
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y python3-devel portaudio-devel
    else
        echo "Unsupported Linux distribution. Please install portaudio manually."
        exit 1
    fi
else
    echo "Unsupported operating system. Please follow manual installation instructions in README.md"
    exit 1
fi

# Create and activate virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment based on OS
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Please activate the virtual environment manually:"
    echo "source venv/bin/activate  # On macOS/Linux"
    echo "venv\\Scripts\\activate    # On Windows"
    exit 1
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install PyAudio separately first
echo "Installing PyAudio..."
pip install pyaudio

# Install requirements
echo "Installing project dependencies..."
pip install -r requirements.txt

# Install Watchdog for better Streamlit performance
echo "Installing Watchdog for better Streamlit performance..."
pip install watchdog

echo "=============================================================="
echo "Setup completed successfully!"
echo "To run the application, use: streamlit run app.py"
echo "=============================================================="
