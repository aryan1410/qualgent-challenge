#!/usr/bin/env python3
"""
Verify Framework Installation
=============================
Checks that all components are properly installed and configured.
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
        import google.adk
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


def check_api_key():
    """Check for API key."""
    print("\n🔍 Checking API key...")
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")
    if api_key:
        print(f"✅ API key found (length: {len(api_key)})")
        return True
    else:
        print("❌ No API key found")
        print("   Set GOOGLE_API_KEY environment variable")
        print("   Get key from: https://aistudio.google.com/apikey")
        return False


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
    
    print("❌ ADB not found")
    print("   Install Android SDK from: https://developer.android.com/studio")
    return False


def check_device():
    """Check for connected Android device."""
    print("\n🔍 Checking for Android device...")
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().split('\n')
        devices = [l for l in lines[1:] if 'device' in l and 'offline' not in l]
        
        if devices:
            print(f"✅ {len(devices)} device(s) connected:")
            for device in devices:
                print(f"   • {device}")
            return True
        else:
            print("⚠️  No devices connected")
            print("   Start an emulator or connect a physical device")
            return False
    except Exception as e:
        print(f"❌ Error checking devices: {e}")
        return False


def check_obsidian():
    """Check if Obsidian is installed on device."""
    print("\n🔍 Checking for Obsidian app...")
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "list", "packages", "md.obsidian"],
            capture_output=True,
            text=True
        )
        if "md.obsidian" in result.stdout:
            print("✅ Obsidian installed on device")
            return True
        else:
            print("⚠️  Obsidian not installed on device")
            print("   Install from Play Store: md.obsidian")
            return False
    except Exception as e:
        print(f"❌ Error checking app: {e}")
        return False


def check_local_modules():
    """Check local module imports."""
    print("\n🔍 Checking local modules...")
    
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        
        from src.mobile_qa_agent.tools.adb_tools import tap, take_screenshot
        print("✅ adb_tools module")
        
        from src.mobile_qa_agent.tools.metrics import MetricsTracker
        print("✅ metrics module")
        
        from src.mobile_qa_agent.agent import root_agent
        print("✅ agent module")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Run: pip install -e .")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("📱 Mobile QA Agent - Framework Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Python", check_python_version()))
    results.append(("Google ADK", check_google_adk()))
    results.append(("Google GenAI", check_google_generativeai()))
    results.append(("API Key", check_api_key()))
    results.append(("ADB", check_adb()))
    results.append(("Device", check_device()))
    results.append(("Obsidian", check_obsidian()))
    results.append(("Local Modules", check_local_modules()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        icon = "✅" if result else "❌"
        print(f"  {icon} {name}")
    
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Framework is ready to use.")
        print("\nNext steps:")
        print("  python -m src.main --list       # List test cases")
        print("  python -m src.main --task 1     # Run test 1")
        print("  adk web                         # Start ADK web UI")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please resolve issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
