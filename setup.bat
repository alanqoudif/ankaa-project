@echo off
:: Setup script for Ankaa Project (ShariaAI - Omani Legal Assistant) on Windows
:: This script automates the installation process and handles common issues

echo Setting up Ankaa Project (ShariaAI - Omani Legal Assistant)...
echo ==============================================================

:: Create virtual environment
echo Creating Python virtual environment...
python -m venv venv

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

:: Upgrade pip
echo Upgrading pip...
pip install --upgrade pip

:: Install pipwin for easier PyAudio installation on Windows
echo Installing pipwin for PyAudio...
pip install pipwin

:: Install PyAudio using pipwin
echo Installing PyAudio...
pipwin install pyaudio
:: Fallback if pipwin fails
if %ERRORLEVEL% NEQ 0 (
    echo Attempting direct PyAudio installation...
    pip install pyaudio
)

:: Install requirements
echo Installing project dependencies...
pip install -r requirements.txt

:: Install Watchdog for better Streamlit performance
echo Installing Watchdog for better Streamlit performance...
pip install watchdog

echo ==============================================================
echo Setup completed successfully!
echo To run the application, use: streamlit run app.py
echo ==============================================================

pause
