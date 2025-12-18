#!/usr/bin/env python3
"""
Mobile QA Agent - Main Entry Point
===================================
Multi-agent system for automated mobile app testing.
Uses Groq's Llama 4 Vision model for UI understanding.

Usage:
    python main.py           # Interactive menu
    python main.py --all     # Run all tests
    python main.py --test 1  # Run specific test (1-4)
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agents import MobileQAOrchestrator, TestResult
from adb_tools import launch_app, press_back, wait, force_stop_app, dismiss_stylus_popup


# Obsidian app package name
OBSIDIAN_PACKAGE = "md.obsidian"

# Test cases for Obsidian app
TEST_CASES = [
    "Open Obsidian, create a new Vault named 'InternVault', and enter the vault.",
    "Create a new note titled 'Meeting Notes' and type the text 'Daily Standup' into the body.",
    "Go to Settings and verify that the 'Appearance' tab icon is the color Red.",
    "Find and click the 'Print to PDF' button in the main file menu."
]

# Expected results for comparison
# Tests 1-2 should PASS (features exist and work)
# Tests 3-4 should FAIL (intentional - to test bug detection)
EXPECTED_RESULTS = {
    0: "PASS",  # Create vault - should work
    1: "PASS",  # Create note - should work  
    2: "FAIL",  # Appearance icon is NOT red (it's monochrome/purple) - BUG
    3: "FAIL",  # Print to PDF doesn't exist in mobile Obsidian - BUG
}


def check_prerequisites() -> bool:
    """Check if all prerequisites are met before running tests."""
    
    print("🔍 Checking prerequisites...\n")
    
    # Check for API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not found!")
        print("   1. Get a free API key from: https://console.groq.com/keys")
        print("   2. Create a .env file with: GROQ_API_KEY=your-key-here")
        return False
    print("✅ Groq API key found")
    
    # Check for ADB
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        lines = result.stdout.strip().split('\n')
        devices = [l for l in lines[1:] if 'device' in l and 'offline' not in l]
        
        if not devices:
            print("❌ No Android device/emulator connected!")
            print("   Please start an Android emulator first.")
            return False
        print(f"✅ Android device connected: {devices[0].split()[0]}")
        
    except FileNotFoundError:
        print("❌ ADB not found!")
        print("   Please install Android SDK platform-tools and add to PATH.")
        return False
    except subprocess.TimeoutExpired:
        print("❌ ADB timed out - emulator may be unresponsive.")
        return False
    
    # Check if Obsidian is installed
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "list", "packages", OBSIDIAN_PACKAGE],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if OBSIDIAN_PACKAGE not in result.stdout:
            print(f"❌ Obsidian not installed!")
            print(f"   Please install Obsidian APK: adb install Obsidian-x.x.x.apk")
            return False
        print("✅ Obsidian app installed")
        
    except Exception as e:
        print(f"⚠️  Could not verify Obsidian installation: {e}")
    
    print("\n✅ All prerequisites met!\n")
    return True


def prepare_device():
    """Prepare the device for testing."""
    print("📱 Preparing device...")
    
    # Force stop Obsidian to ensure clean state
    force_stop_app(OBSIDIAN_PACKAGE)
    wait(1)
    
    # Launch Obsidian
    launch_app(OBSIDIAN_PACKAGE)
    wait(3)
    
    # Dismiss any initial popups (like stylus popup)
    dismiss_stylus_popup()
    wait(0.5)
    
    print("✅ Device ready\n")


def save_results(results: list, filename: str):
    """Save test results to a JSON file."""
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "total_tests": len(results),
        "passed": sum(1 for r in results if r.final_result == "PASS"),
        "failed": sum(1 for r in results if r.final_result == "FAIL"),
        "results": []
    }
    
    for i, result in enumerate(results):
        expected = EXPECTED_RESULTS.get(i, "UNKNOWN")
        output["results"].append({
            "test_number": i + 1,
            "test_case": result.test_case,
            "expected_result": expected,
            "actual_result": result.final_result,
            "matches_expected": result.final_result == expected,
            "result_type": result.result_type,
            "reasoning": result.reasoning,
            "bug_report": result.bug_report,
            "steps_taken": result.steps_taken,
            "duration_seconds": result.duration_seconds
        })
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")


def print_comparison(results: list):
    """Print expected vs actual results comparison."""
    
    print("\n" + "="*60)
    print("📊 EXPECTED vs ACTUAL RESULTS")
    print("="*60)
    
    test_names = [
        "Create Vault",
        "Create Note", 
        "Appearance Icon Color",
        "Print to PDF"
    ]
    
    all_match = True
    for i, result in enumerate(results):
        expected = EXPECTED_RESULTS.get(i, "UNKNOWN")
        actual = result.final_result
        match = "✅" if expected == actual else "❌"
        if expected != actual:
            all_match = False
        
        name = test_names[i] if i < len(test_names) else f"Test {i+1}"
        print(f"  {match} Test {i+1} ({name}):")
        print(f"      Expected: {expected}, Got: {actual}")
    
    print()
    if all_match:
        print("🎉 All tests matched expected results!")
    else:
        print("⚠️  Some tests did not match expected results.")


def interactive_menu(orchestrator: MobileQAOrchestrator):
    """Show interactive menu for running tests."""
    
    while True:
        print("\n" + "="*60)
        print("📋 MOBILE QA AGENT - TEST MENU")
        print("="*60)
        print("\nAvailable Test Cases:")
        
        for i, tc in enumerate(TEST_CASES, 1):
            expected = EXPECTED_RESULTS.get(i-1, "?")
            status = "🟢" if expected == "PASS" else "🔴"
            print(f"  {i}. {status} [{expected}] {tc[:50]}...")
        
        print("\n  5. 🚀 Run ALL tests")
        print("  6. 🔄 Reset Obsidian (clear app data)")
        print("  0. 🚪 Exit")
        
        try:
            choice = input("\nSelect option (0-6): ").strip()
            
            if choice == "0":
                print("\n👋 Goodbye!")
                break
            
            elif choice == "6":
                print("\n🔄 Resetting Obsidian...")
                from adb_tools import clear_app_data
                clear_app_data(OBSIDIAN_PACKAGE)
                print("✅ App data cleared. Vault will need to be recreated.")
                continue
            
            elif choice == "5":
                # Run all tests
                prepare_device()
                results = orchestrator.run_test_suite(TEST_CASES)
                print_comparison(results)
                save_results(results, "test_results_all.json")
                
            elif choice in ["1", "2", "3", "4"]:
                idx = int(choice) - 1
                
                prepare_device()
                result = orchestrator.run_test(TEST_CASES[idx])
                
                # Show comparison
                expected = EXPECTED_RESULTS.get(idx, "UNKNOWN")
                match = "✅" if result.final_result == expected else "❌"
                print(f"\n{match} Expected: {expected}, Got: {result.final_result}")
                
                save_results([result], f"test_result_{choice}.json")
                
            else:
                print("❌ Invalid option. Please enter 0-6.")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Mobile QA Agent for Obsidian")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--test", type=int, choices=[1, 2, 3, 4], help="Run specific test")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file")
    args = parser.parse_args()
    
    # Print banner
    print("\n" + "="*60)
    print("🤖 MOBILE QA AGENT")
    print("   Multi-Agent System for Automated Mobile Testing")
    print("   Powered by Groq + Llama 4 Vision")
    print("="*60)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Initialize orchestrator
    api_key = os.getenv("GROQ_API_KEY")
    orchestrator = MobileQAOrchestrator(api_key)
    
    # Handle command line arguments
    if args.all:
        prepare_device()
        results = orchestrator.run_test_suite(TEST_CASES)
        print_comparison(results)
        output_file = args.output or "test_results_all.json"
        save_results(results, output_file)
        
    elif args.test:
        idx = args.test - 1
        prepare_device()
        result = orchestrator.run_test(TEST_CASES[idx])
        
        expected = EXPECTED_RESULTS.get(idx, "UNKNOWN")
        match = "✅" if result.final_result == expected else "❌"
        print(f"\n{match} Expected: {expected}, Got: {result.final_result}")
        
        output_file = args.output or f"test_result_{args.test}.json"
        save_results([result], output_file)
        
    else:
        # Interactive mode
        interactive_menu(orchestrator)


if __name__ == "__main__":
    main()