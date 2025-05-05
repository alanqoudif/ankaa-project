# Installation Guide for Ankaa Project (ShariaAI)

This guide provides detailed instructions for installing and running the Ankaa Project on different operating systems.

## Table of Contents
- [Quick Start (Automated Setup)](#quick-start-automated-setup)
- [Manual Installation](#manual-installation)
  - [Prerequisites](#prerequisites)
  - [Step-by-Step Installation](#step-by-step-installation)
- [Troubleshooting](#troubleshooting)
- [Running the Application](#running-the-application)

## Quick Start (Automated Setup)

For your convenience, we've provided setup scripts that automate the installation process:

### macOS/Linux:
```bash
git clone https://github.com/alanqoudif/ankaa-project.git
cd ankaa-project
chmod +x setup.sh
./setup.sh
```

### Windows:
```bash
git clone https://github.com/alanqoudif/ankaa-project.git
cd ankaa-project
setup.bat
```

## Manual Installation

If you prefer to install manually or encounter issues with the automated setup, follow these steps:

### Prerequisites

Before installing the Python packages, you need to install system dependencies for PyAudio:

#### macOS:
```bash
brew install portaudio
```

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install python3-dev portaudio19-dev
```

#### CentOS/RHEL:
```bash
sudo yum install python3-devel portaudio-devel
```

#### Windows:
Windows users should install Visual C++ Build Tools and then use pipwin:
```bash
pip install pipwin
pipwin install pyaudio
```

### Step-by-Step Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alanqoudif/ankaa-project.git
   cd ankaa-project
   ```

2. Create a virtual environment:
   ```bash
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```

4. Install PyAudio separately first:
   ```bash
   pip install pyaudio
   ```

5. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

6. Install Watchdog for better Streamlit performance (optional):
   ```bash
   pip install watchdog
   ```

## Troubleshooting

### Common Issues and Solutions

#### PyAudio Installation Fails

**Error**: `Error: Could not build wheels for pyaudio`

**Solution**:
- Ensure you've installed the system dependencies (portaudio)
- Try installing with pipwin on Windows: `pipwin install pyaudio`
- On macOS, if using Homebrew doesn't work, try: `CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" pip install pyaudio`

#### Missing Module Error When Running

**Error**: `ModuleNotFoundError: No module named 'pyaudio'`

**Solution**:
- Make sure your virtual environment is activated
- Install PyAudio separately: `pip install pyaudio`
- If using Anaconda, try: `conda install -c anaconda pyaudio`

#### Streamlit-WebRTC Issues

**Error**: Problems with streamlit-webrtc or av packages

**Solution**:
- Install these packages separately: `pip install streamlit-webrtc av`
- Ensure you have the required system libraries for av: `apt-get install ffmpeg` (Linux) or `brew install ffmpeg` (macOS)

## Running the Application

Once installation is complete, run the application:

```bash
streamlit run app.py
```

The application will be available at http://localhost:8501 in your web browser.

## Additional Notes

- The application requires an internet connection for some features like OpenAI API access
- For production deployment, consider using Docker (see Dockerfile in the repository)
- If you encounter any other issues, please open an issue on the GitHub repository
