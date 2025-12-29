#!/bin/bash
# ============================================================
# 📱 Mobile QA Agent - Setup Script
# ============================================================
# AI-Powered Mobile Testing with Google ADK
# 
# This script sets up the complete development environment
# including Python dependencies, ADB verification, and
# configuration files.
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}📱 Mobile QA Agent - Setup${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Print header
print_header

# -----------------------------------------------------------------------------
# Step 1: Check Python Version
# -----------------------------------------------------------------------------
print_step "Checking Python version..."

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    print_error "Python 3.10 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi
print_success "Python $PYTHON_VERSION found"

# -----------------------------------------------------------------------------
# Step 2: Create Virtual Environment
# -----------------------------------------------------------------------------
print_step "Setting up virtual environment..."

if [ -d ".venv" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
else
    $PYTHON_CMD -m venv .venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    source .venv/Scripts/activate
else
    # Linux/Mac
    source .venv/bin/activate
fi
print_success "Virtual environment activated"

# -----------------------------------------------------------------------------
# Step 3: Upgrade pip
# -----------------------------------------------------------------------------
print_step "Upgrading pip..."
pip install --upgrade pip --quiet
print_success "pip upgraded"

# -----------------------------------------------------------------------------
# Step 4: Install Dependencies
# -----------------------------------------------------------------------------
print_step "Installing dependencies..."

# Install main requirements
pip install -r requirements.txt --quiet

# Install package in editable mode
pip install -e . --quiet

print_success "Dependencies installed"

# -----------------------------------------------------------------------------
# Step 5: Check ADB Installation
# -----------------------------------------------------------------------------
print_step "Checking ADB installation..."

if command -v adb &> /dev/null; then
    ADB_VERSION=$(adb version | head -n1)
    print_success "ADB found: $ADB_VERSION"
else
    print_warning "ADB not found in PATH"
    echo ""
    echo "   Please install Android SDK Platform Tools:"
    echo "   - Download: https://developer.android.com/studio/releases/platform-tools"
    echo "   - Or install Android Studio: https://developer.android.com/studio"
    echo ""
fi

# -----------------------------------------------------------------------------
# Step 6: Check Connected Devices
# -----------------------------------------------------------------------------
print_step "Checking for connected Android devices..."

if command -v adb &> /dev/null; then
    DEVICE_COUNT=$(adb devices | grep -c "device$" || true)
    
    if [ "$DEVICE_COUNT" -gt 0 ]; then
        print_success "Found $DEVICE_COUNT connected device(s):"
        adb devices -l | grep "device" | grep -v "List"
    else
        print_warning "No Android device/emulator connected"
        echo ""
        echo "   To start an emulator:"
        echo "   - Open Android Studio → AVD Manager → Start emulator"
        echo "   - Or use command: emulator -avd <avd_name>"
        echo ""
    fi
fi

# -----------------------------------------------------------------------------
# Step 7: Setup Environment File
# -----------------------------------------------------------------------------
print_step "Setting up environment configuration..."

if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# =============================================================================
# Mobile QA Agent - Environment Configuration
# =============================================================================

# -----------------------------------------------------------------------------
# LLM API Keys (at least one required)
# -----------------------------------------------------------------------------

# Google Gemini (recommended) - Get from: https://aistudio.google.com/apikey
GOOGLE_API_KEY=your_google_api_key_here

# OpenAI (alternative) - Get from: https://platform.openai.com/api-keys
# OPENAI_API_KEY=your_openai_api_key_here

# Together AI (alternative) - Get from: https://api.together.xyz/
# TOGETHER_API_KEY=your_together_api_key_here

# -----------------------------------------------------------------------------
# App Configuration
# -----------------------------------------------------------------------------
APP_PACKAGE=md.obsidian
EOF
    print_success "Created .env file"
    print_warning "Please edit .env and add your API key(s)"
else
    print_success ".env file already exists"
fi

# -----------------------------------------------------------------------------
# Step 8: Create Required Directories
# -----------------------------------------------------------------------------
print_step "Creating required directories..."

mkdir -p results
mkdir -p logs

print_success "Directories created"

# -----------------------------------------------------------------------------
# Step 9: Verify Installation
# -----------------------------------------------------------------------------
print_step "Verifying installation..."

# Check if Google ADK is importable
if $PYTHON_CMD -c "from google.adk.agents import Agent; print('ADK OK')" 2>/dev/null; then
    print_success "Google ADK installed correctly"
else
    print_warning "Google ADK import failed - may need API key configured"
fi

# Check if our modules are importable
if $PYTHON_CMD -c "from src.mobile_qa_agent.agent import create_test_agent; print('Agent OK')" 2>/dev/null; then
    print_success "Mobile QA Agent modules loaded"
else
    print_warning "Module import issues - check installation"
fi

# -----------------------------------------------------------------------------
# Final Summary
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo "📋 Quick Start Guide:"
echo ""
echo "   1. Configure API Key:"
echo "      Edit .env and add your GOOGLE_API_KEY"
echo "      Get one from: https://aistudio.google.com/apikey"
echo ""
echo "   2. Start Android Emulator:"
echo "      Open Android Studio → AVD Manager → Start"
echo "      Or: emulator -avd <your_avd_name>"
echo ""
echo "   3. Install Obsidian on Device:"
echo "      adb install obsidian.apk"
echo "      Or install from Play Store"
echo ""
echo "   4. Activate Environment & Run:"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "      .venv\\Scripts\\activate"
else
    echo "      source .venv/bin/activate"
fi
echo ""
echo "   5. Run Tests:"
echo "      python src/main.py --list           # List all tests"
echo "      python src/main.py --task 1         # Run test 1"
echo "      python src/main.py --task all       # Run all tests"
echo ""
echo "   6. View Results:"
echo "      Results are saved in ./results/ directory"
echo ""
echo -e "${BLUE}============================================================${NC}"
echo ""