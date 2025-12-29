#!/usr/bin/env python3
"""
Verify Framework Installation
=============================
Checks that all components are properly installed and configured.

Run this script to diagnose any setup issues:
    python verify_framework.py
"""

import sys
import os
import subprocess


def check_python_version():
    """Check Python version."""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python 3.10+ required. Found: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_google_adk():
    """Check Google ADK installation."""
    print("\n🔍 Checking Google ADK...")
    try:
        from google.adk.agents import Agent
        from google.adk.runners import InMemoryRunner
        print(f"✅ Google ADK installed")
        return True
    except ImportError as e:
        print(f"❌ Google ADK not installed: {e}")
        print("   Run: pip install google-adk")
        return False


def check_google_generativeai():
    """Check Google Generative AI installation."""
    print("\n🔍 Checking Google Generative AI...")
    try:
        import google.generativeai
        print(f"✅ Google Generative AI installed")
        return True
    except ImportError as e:
        print(f"❌ Google Generative AI not installed: {e}")
        print("   Run: pip install google-generativeai")
        return False


def check_pillow():
    """Check Pillow installation (for screenshot compression)."""
    print("\n🔍 Checking Pillow (image processing)...")
    try:
        from PIL import Image
        print(f"✅ Pillow installed")
        return True
    except ImportError as e:
        print(f"⚠️  Pillow not installed: {e}")
        print("   Screenshots will work but won't be compressed")
        print("   Run: pip install pillow")
        return False


def check_api_keys():
    """Check for API keys."""
    print("\n🔍 Checking API keys...")
    
    # Load .env if exists
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if value and not value.startswith('your_'):
                        os.environ[key.strip()] = value.strip()
    
    google_key = os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    together_key = os.getenv("TOGETHER_API_KEY")
    
    found_any = False
    
    if google_key and not google_key.startswith('your_'):
        print(f"✅ GOOGLE_API_KEY found (length: {len(google_key)})")
        found_any = True
    
    if openai_key and not openai_key.startswith('your_'):
        print(f"✅ OPENAI_API_KEY found (length: {len(openai_key)})")
        found_any = True
    
    if together_key and not together_key.startswith('your_'):
        print(f"✅ TOGETHER_API_KEY found (length: {len(together_key)})")
        found_any = True
    
    if not found_any:
        print("❌ No API key found")
        print("   Set one of: GOOGLE_API_KEY, OPENAI_API_KEY, or TOGETHER_API_KEY")
        print("   Edit .env file or set environment variable")
        print("   Get Google key from: https://aistudio.google.com/apikey")
        return False
    
    return True


def check_adb():
    """Check ADB installation."""
    print("\n🔍 Checking ADB...")
    try:
        result = subprocess.run(
            ["adb", "version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ {version_line}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ ADB not found in PATH")
    print("   Install Android SDK Platform Tools:")
    print("   https://developer.android.com/studio/releases/platform-tools")
    return False


def check_device():
    """Check for connected Android device."""
    print("\n🔍 Checking for Android device/emulator...")
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().split('\n')
        devices = [l for l in lines[1:] if 'device' in l and 'offline' not in l and l.strip()]
        
        if devices:
            print(f"✅ {len(devices)} device(s) connected:")
            for device in devices:
                print(f"   • {device}")
            return True
        else:
            print("⚠️  No devices connected")
            print("   Start an emulator: emulator -avd <avd_name>")
            print("   Or connect a physical device with USB debugging enabled")
            return False
    except Exception as e:
        print(f"❌ Error checking devices: {e}")
        return False


def check_obsidian():
    """Check if Obsidian is installed on device."""
    print("\n🔍 Checking for Obsidian app on device...")
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "list", "packages", "md.obsidian"],
            capture_output=True,
            text=True
        )
        if "md.obsidian" in result.stdout:
            print("✅ Obsidian (md.obsidian) installed on device")
            return True
        else:
            print("⚠️  Obsidian not installed on device")
            print("   Install from Play Store or download APK")
            return False
    except Exception as e:
        print(f"⚠️  Could not check app (device may not be connected): {e}")
        return False


def check_local_modules():
    """Check local module imports."""
    print("\n🔍 Checking local modules...")
    
    try:
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Check adb_tools
        from src.mobile_qa_agent.tools.adb_tools import tap, get_ui_hierarchy, take_screenshot_compressed
        print("✅ adb_tools module")
        
        # Check metrics
        from src.mobile_qa_agent.tools.metrics import MetricsTracker, IDEAL_WORKFLOWS
        print(f"✅ metrics module ({len(IDEAL_WORKFLOWS)} ideal workflows defined)")
        
        # Check agent
        from src.mobile_qa_agent.agent import create_test_agent, get_test_prompt, ALL_TOOLS
        print(f"✅ agent module ({len(ALL_TOOLS)} tools available)")
        
        # Check main
        from src.main import TEST_CASES, MobileQARunner
        print(f"✅ main module ({len(TEST_CASES)} test cases defined)")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Run: pip install -e .")
        return False


def check_env_file():
    """Check if .env file exists."""
    print("\n🔍 Checking .env file...")
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    
    if os.path.exists(env_file):
        print(f"✅ .env file exists")
        return True
    else:
        print("⚠️  .env file not found")
        print("   Create from template: cp .env.example .env")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("📱 Mobile QA Agent - Framework Verification")
    print("=" * 60)
    
    results = []
    
    # Critical checks
    results.append(("Python Version", check_python_version()))
    results.append(("Google ADK", check_google_adk()))
    results.append(("Google GenAI", check_google_generativeai()))
    results.append(("Pillow", check_pillow()))
    results.append((".env File", check_env_file()))
    results.append(("API Key(s)", check_api_keys()))
    results.append(("ADB", check_adb()))
    results.append(("Android Device", check_device()))
    results.append(("Obsidian App", check_obsidian()))
    results.append(("Local Modules", check_local_modules()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Verification Summary")
    print("=" * 60)
    
    critical_checks = ["Python Version", "Google ADK", "API Key(s)", "ADB", "Local Modules"]
    
    passed = 0
    critical_passed = 0
    total = len(results)
    critical_total = len(critical_checks)
    
    for name, result in results:
        icon = "✅" if result else "❌" if name in critical_checks else "⚠️"
        status = "PASS" if result else "FAIL" if name in critical_checks else "WARN"
        print(f"  {icon} {name}: {status}")
        
        if result:
            passed += 1
            if name in critical_checks:
                critical_passed += 1
        elif name in critical_checks:
            pass  # Don't count warnings
    
    print(f"\nResult: {passed}/{total} checks passed ({critical_passed}/{critical_total} critical)")
    
    if critical_passed == critical_total:
        print("\n🎉 All critical checks passed! Framework is ready to use.")
        print("\n" + "-" * 60)
        print("Quick Start:")
        print("-" * 60)
        print("  python src/main.py --list        # List all test cases")
        print("  python src/main.py --task 1      # Run test 1 (Create Vault)")
        print("  python src/main.py --task all    # Run all tests")
        print("-" * 60)
        return 0
    else:
        print("\n⚠️  Some critical checks failed. Please resolve issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())