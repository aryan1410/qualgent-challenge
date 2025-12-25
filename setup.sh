#!/bin/bash
# ============================================================
# Mobile QA Agent - Setup Script
# ============================================================
# This script sets up the development environment for the
# Mobile QA Agent framework built with Google ADK.
# ============================================================

set -e  # Exit on error

echo "============================================================"
echo "📱 Mobile QA Agent - Setup"
echo "============================================================"

# Check Python version
echo "🔍 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping creation."
else
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔄 Activating virtual environment..."
source .venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Install the package in editable mode
echo ""
echo "📦 Installing mobile_qa_agent package..."
pip install -e .
echo "✅ Package installed"

# Check for Android SDK / ADB
echo ""
echo "🔍 Checking for ADB..."
if command -v adb &> /dev/null; then
    ADB_VERSION=$(adb version | head -n1)
    echo "✅ ADB found: $ADB_VERSION"
else
    echo "⚠️  ADB not found. Please install Android SDK."
    echo "   Download from: https://developer.android.com/studio"
fi

# Check for connected devices
echo ""
echo "🔍 Checking for connected Android devices..."
if adb devices | grep -q "device$"; then
    echo "✅ Android device connected"
    adb devices -l
else
    echo "⚠️  No Android device connected."
    echo "   Start an emulator or connect a physical device."
fi

# Setup .env file
echo ""
echo "🔑 Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please edit .env and add your GOOGLE_API_KEY"
else
    echo "✅ .env file already exists"
fi

# Create results directory
echo ""
echo "📁 Creating results directory..."
mkdir -p results
echo "✅ Results directory ready"

# Final instructions
echo ""
echo "============================================================"
echo "✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your GOOGLE_API_KEY"
echo "     Get one from: https://aistudio.google.com/apikey"
echo ""
echo "  2. Start an Android emulator or connect a device"
echo "     Verify with: adb devices"
echo ""
echo "  3. Install Obsidian on the device/emulator"
echo "     Package: md.obsidian"
echo ""
echo "  4. Activate the environment and run tests:"
echo "     source .venv/bin/activate"
echo "     python -m src.main --list          # List tests"
echo "     python -m src.main --task 1        # Run test 1"
echo "     python -m src.main --task all      # Run all tests"
echo ""
echo "  5. Or use ADK web interface:"
echo "     adk web"
echo ""
echo "============================================================"
