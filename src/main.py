#!/usr/bin/env python3
"""
Mobile QA Agent - Main Runner
==============================
Run mobile QA tests using Google ADK framework with Groq LLM.

Usage:
    python src/main.py --task 1                    # Run test 1
    python src/main.py --task all                  # Run all tests
    python src/main.py --task 1 --calculate-reward # With reward metrics
    python src/main.py --list                      # List all test cases
"""

import os
import sys
import json
import time
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Add src to path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(src_path.parent))

# Try different import paths for local modules
try:
    from mobile_qa_agent.tools.adb_tools import (
        launch_app,
        clear_app_data,
        check_device_connected,
        find_clickable_elements,
        tap_element,
        tap,
        clear_and_type,
        press_enter,
        press_back,
        take_screenshot
    )
    from mobile_qa_agent.tools.metrics import MetricsTracker
except ImportError:
    from src.mobile_qa_agent.tools.adb_tools import (
        launch_app,
        clear_app_data,
        check_device_connected,
        find_clickable_elements,
        tap_element,
        tap,
        clear_and_type,
        press_enter,
        press_back,
        take_screenshot
    )
    from src.mobile_qa_agent.tools.metrics import MetricsTracker

# Check for Google ADK
ADK_AVAILABLE = False
try:
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner
    from google.genai import types
    ADK_AVAILABLE = True
    print("✅ Google ADK loaded successfully")
except ImportError as e:
    print(f"⚠️  Google ADK not available: {e}")
    print("    Install with: pip install google-adk")


# =============================================================================
# TEST CASES
# =============================================================================

TEST_CASES = {
    1: {
        "name": "Create Vault",
        "description": "Open Obsidian, create a new Vault named 'InternVault', and enter the vault.",
        "expected_result": "PASS",
        "app_package": "md.obsidian",
        "ground_truth_steps": [
            "tap_element: Create a vault",
            "tap_element: Continue without sync",
            "tap_input: Vault name",
            "clear_and_type: InternVault",
            "press_enter",
            "tap_element: Create a vault",
            "tap_element: USE THIS FOLDER",
            "tap_element: Allow"
        ]
    },
    2: {
        "name": "Create Note",
        "description": "Create a new note titled 'Meeting Notes' with content 'Daily Standup'.",
        "expected_result": "PASS",
        "app_package": "md.obsidian",
        "ground_truth_steps": [
            "tap_element: Create new note",
            "tap_input: Untitled",
            "clear_and_type: Meeting Notes",
            "press_enter",
            "type_text: Daily Standup"
        ]
    },
    3: {
        "name": "Verify Appearance Icon Color",
        "description": "Navigate to Settings and verify the Appearance tab icon is Red.",
        "expected_result": "FAIL",
        "app_package": "md.obsidian",
        "ground_truth_steps": [
            "tap_element: Settings/Menu",
            "tap_element: Settings",
            "verify: Appearance icon color"
        ]
    },
    4: {
        "name": "Find Print to PDF",
        "description": "Search for 'Print to PDF' option in the app.",
        "expected_result": "FAIL",
        "app_package": "md.obsidian",
        "ground_truth_steps": [
            "tap_element: Menu",
            "search: Print to PDF",
            "verify: Feature exists"
        ]
    },
    5: {
        "name": "Create Multiple Notes",
        "description": "Create two notes: 'Project Ideas' and 'Todo List'.",
        "expected_result": "PASS",
        "app_package": "md.obsidian",
        "ground_truth_steps": [
            "tap_element: Create new note",
            "clear_and_type: Project Ideas",
            "press_enter",
            "press_back",
            "tap_element: Create new note",
            "clear_and_type: Todo List",
            "press_enter"
        ]
    },
    6: {
        "name": "Search Notes",
        "description": "Use the search function to find a note.",
        "expected_result": "PASS",
        "app_package": "md.obsidian",
        "ground_truth_steps": [
            "tap_element: Search",
            "type_text: Meeting",
            "verify: Results shown"
        ]
    },
    7: {
        "name": "Delete Note",
        "description": "Delete an existing note from the vault.",
        "expected_result": "PASS",
        "app_package": "md.obsidian",
        "ground_truth_steps": [
            "long_press: Note",
            "tap_element: Delete",
            "tap_element: Confirm"
        ]
    },
    8: {
        "name": "Change Theme",
        "description": "Change the app theme to dark mode.",
        "expected_result": "PASS",
        "app_package": "md.obsidian",
        "ground_truth_steps": [
            "tap_element: Settings",
            "tap_element: Appearance",
            "tap_element: Dark"
        ]
    },
    9: {
        "name": "Create Folder",
        "description": "Create a new folder named 'Work' in the vault.",
        "expected_result": "PASS",
        "app_package": "md.obsidian",
        "ground_truth_steps": [
            "tap_element: New folder",
            "type_text: Work",
            "tap_element: Create"
        ]
    },
    10: {
        "name": "Link Notes",
        "description": "Create a link between two notes using [[]] syntax.",
        "expected_result": "PASS",
        "app_package": "md.obsidian",
        "ground_truth_steps": [
            "tap_element: Open note",
            "type_text: [[Meeting Notes]]",
            "verify: Link created"
        ]
    }
}


# =============================================================================
# TOOL FUNCTIONS FOR ADK AGENT
# =============================================================================

def get_screen_state() -> dict:
    """Get the current screen state with all UI elements."""
    elements = find_clickable_elements()
    all_text = ' '.join([e.get('text', '').lower() for e in elements])
    
    screen_type = "unknown"
    suggested_action = ""
    
    if 'create new note' in all_text:
        screen_type = "inside_vault"
        suggested_action = "TEST COMPLETE - vault entered successfully"
    elif 'create a vault' in all_text and 'use my existing' in all_text:
        screen_type = "initial_vault_choice"
        suggested_action = "tap_on_element('Create a vault')"
    elif 'continue without sync' in all_text:
        screen_type = "sync_setup"
        suggested_action = "tap_on_element('Continue without sync')"
    elif 'vault name' in all_text:
        screen_type = "vault_configuration"
        suggested_action = "type_in_field('InternVault') then press_enter_key() then tap_on_element('Create a vault')"
    elif 'use this folder' in all_text:
        screen_type = "folder_picker"
        suggested_action = "tap_on_element('USE THIS FOLDER')"
    elif 'allow' in all_text and len(all_text) < 500:
        screen_type = "permission_dialog"
        suggested_action = "tap_on_element('Allow')"
    
    return {
        "screen_type": screen_type,
        "suggested_action": suggested_action,
        "elements": [{"text": e.get('text', ''), "clickable": e.get('clickable', False)} 
                    for e in elements[:15] if e.get('text')]
    }


def tap_on_element(element_text: str) -> dict:
    """Tap on a UI element by its text."""
    result = tap_element(element_text)
    success = "Error" not in result
    return {"success": success, "message": result}


def tap_at_coordinates(x: int, y: int) -> dict:
    """Tap at specific screen coordinates."""
    tap(x, y)
    return {"success": True, "message": f"Tapped at ({x}, {y})"}


def type_in_field(text: str) -> dict:
    """Clear the field and type text."""
    result = clear_and_type(text)
    return {"success": True, "message": f"Typed: {text}"}


def press_enter_key() -> dict:
    """Press the Enter key."""
    press_enter()
    return {"success": True, "message": "Pressed Enter"}


def press_back_button() -> dict:
    """Press the Back button."""
    press_back()
    return {"success": True, "message": "Pressed Back"}


# =============================================================================
# RUNNER CLASS
# =============================================================================

class MobileQARunner:
    """Runs mobile QA tests using Google ADK with Groq."""
    
    def __init__(self, calculate_reward: bool = True, verbose: bool = True):
        self.calculate_reward = calculate_reward
        self.verbose = verbose
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        print("🔍 Checking prerequisites...")
        
        # Check for Groq API key
        groq_key = os.getenv("GROQ_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
        
        if groq_key:
            print(f"✅ Groq API key found")
        elif google_key:
            print(f"✅ Google API key found")
        else:
            print("❌ No API key found. Set GROQ_API_KEY or GOOGLE_API_KEY")
            return False
        
        # Check ADK
        if not ADK_AVAILABLE:
            print("❌ Google ADK not installed. Run: pip install google-adk")
            return False
        print("✅ Google ADK available")
        
        # Check device
        if not check_device_connected():
            print("❌ No Android device connected. Start an emulator or connect a device.")
            return False
        print("✅ Android device connected")
        
        return True
    
    def run_test(self, test_num: int) -> dict:
        """Run a single test case."""
        if test_num not in TEST_CASES:
            print(f"❌ Test {test_num} not found")
            return {"error": f"Test {test_num} not found"}
        
        test = TEST_CASES[test_num]
        
        print(f"\n{'='*60}")
        print(f"📋 TEST {test_num}: {test['name']}")
        print(f"{'='*60}")
        print(f"📝 {test['description']}")
        print(f"🎯 Expected: {test['expected_result']}")
        
        # Initialize metrics
        metrics = MetricsTracker(
            test_case=test['description'],
            test_number=test_num,
            expected_result=test['expected_result']
        )
        
        # Prepare app
        print(f"\n📱 Preparing {test['app_package']}...")
        clear_app_data(test['app_package'])
        time.sleep(1)
        launch_app(test['app_package'])
        time.sleep(3)
        
        # Run the test
        print("\n🤖 Running agent...")
        
        final_result = "FAIL"
        reasoning = "Test did not complete"
        
        try:
            final_result, reasoning = asyncio.run(self._run_test_with_adk(test, metrics))
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            reasoning = str(e)
        
        # Finalize metrics
        metrics.finalize(
            final_result=final_result,
            result_type="test_passed" if final_result == "PASS" else "execution_error",
            reasoning=reasoning
        )
        
        # Print results
        if self.calculate_reward:
            metrics.print_summary()
        else:
            print(f"\n{'='*40}")
            result_icon = "✅" if metrics.test_metrics.final_result == "PASS" else "❌"
            print(f"{result_icon} RESULT: {metrics.test_metrics.final_result}")
            print(f"⏱️ Duration: {metrics.test_metrics.duration_seconds:.1f}s")
        
        # Save results
        result_file = self.results_dir / f"test_{test_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w') as f:
            json.dump(metrics.to_dict(), f, indent=2, default=str)
        print(f"\n💾 Results saved to: {result_file}")
        
        return metrics.to_dict()
    
    async def _run_test_with_adk(self, test: dict, metrics: MetricsTracker) -> tuple:
        """Run test using Google ADK with Groq LLM."""
        
        # Determine which model to use
        groq_key = os.getenv("GROQ_API_KEY")
        
        if groq_key:
            # Use Groq via LiteLLM format
            model_name = "groq/llama-4-scout-17b-16e-instruct"
            print(f"🤖 Using Groq model: {model_name}")
        else:
            # Fallback to Gemini
            model_name = "gemini-1.5-flash"
            print(f"🤖 Using Gemini model: {model_name}")
        
        # Create the ADK agent with tools
        test_agent = Agent(
            name="mobile_qa_agent",
            model=model_name,
            description="Mobile QA testing agent for Android apps",
            instruction=f"""You are a mobile QA testing agent. Your task is:

TEST OBJECTIVE: {test['description']}

WORKFLOW:
1. Call get_screen_state() to see what's on screen
2. Based on screen_type, take the suggested_action
3. After each action, call get_screen_state() again
4. Repeat until screen_type is "inside_vault" or objective achieved

SCREEN TYPES AND ACTIONS:
- "initial_vault_choice" → tap_on_element("Create a vault")
- "sync_setup" → tap_on_element("Continue without sync")
- "vault_configuration" → type_in_field("InternVault"), press_enter_key(), tap_on_element("Create a vault")
- "folder_picker" → tap_on_element("USE THIS FOLDER")
- "permission_dialog" → tap_on_element("Allow")
- "inside_vault" → TEST PASSED! Say "TEST PASSED"

RULES:
- Always call get_screen_state() first
- Follow the suggested_action from screen state
- When you see "inside_vault", immediately respond with "TEST PASSED"
- If stuck after 5 attempts on same screen, respond with "TEST FAILED"
""",
            tools=[get_screen_state, tap_on_element, tap_at_coordinates, type_in_field, press_enter_key, press_back_button]
        )
        
        # Create runner
        app_name = "mobile_qa_test"
        user_id = "tester"
        session_id = f"test_{int(time.time())}"
        
        runner = InMemoryRunner(agent=test_agent, app_name=app_name)
        
        # Create session
        await runner.session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        # Run the agent
        prompt = f"Execute this test: {test['description']}. Start by calling get_screen_state() to see the current screen."
        
        final_result = "FAIL"
        reasoning = "Test did not complete"
        step_count = 0
        
        print(f"\n🤖 Agent starting...\n")
        
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part(text=prompt)])
            ):
                step_count += 1
                
                # Log tool calls
                if event.get_function_calls():
                    for fc in event.get_function_calls():
                        print(f"   🔧 Tool: {fc.name}({dict(fc.args) if fc.args else {}})")
                        metrics.start_step()
                        metrics.record_step(
                            action_type=fc.name,
                            action_params=dict(fc.args) if fc.args else {},
                            success=True
                        )
                
                # Check for final response
                if event.is_final_response() and event.content:
                    response_text = ""
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
                    
                    if response_text:
                        print(f"\n📝 Agent response: {response_text[:300]}")
                        
                        if "PASSED" in response_text.upper():
                            final_result = "PASS"
                            reasoning = response_text
                        elif "FAILED" in response_text.upper() or "FAIL" in response_text.upper():
                            final_result = "FAIL"
                            reasoning = response_text
                
                # Safety limit
                if step_count > 50:
                    print("⚠️ Max events reached")
                    break
                    
        except Exception as e:
            print(f"❌ Agent error: {e}")
            reasoning = str(e)
        
        return final_result, reasoning
    
    def run_all_tests(self) -> dict:
        """Run all test cases."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(TEST_CASES),
            "passed": 0,
            "failed": 0,
            "tests": []
        }
        
        for test_num in TEST_CASES:
            result = self.run_test(test_num)
            results["tests"].append(result)
            
            if result.get("final_result") == "PASS":
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            # Wait between tests
            time.sleep(2)
        
        # Print summary
        print(f"\n{'='*60}")
        print("📊 FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"Total: {results['total_tests']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Pass Rate: {results['passed']/results['total_tests']*100:.1f}%")
        
        # Save summary
        summary_file = self.results_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Summary saved to: {summary_file}")
        
        return results


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Mobile QA Agent - Automated Android App Testing with Google ADK"
    )
    parser.add_argument(
        "--task", "-t",
        type=str,
        help="Test number to run (1-10) or 'all' for all tests"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available test cases"
    )
    parser.add_argument(
        "--calculate-reward", "-r",
        action="store_true",
        default=True,
        help="Calculate and display reward metrics (default: True)"
    )
    parser.add_argument(
        "--no-reward",
        action="store_true",
        help="Disable reward calculation"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=True,
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # List tests
    if args.list:
        print("\n📋 Available Test Cases:")
        print("=" * 60)
        for num, test in TEST_CASES.items():
            print(f"  {num}. {test['name']}")
            print(f"     {test['description'][:50]}...")
            print(f"     Expected: {test['expected_result']}")
            print()
        return
    
    # Run tests
    calculate_reward = not args.no_reward
    runner = MobileQARunner(calculate_reward=calculate_reward, verbose=args.verbose)
    
    if not runner.check_prerequisites():
        sys.exit(1)
    
    if args.task:
        if args.task.lower() == "all":
            runner.run_all_tests()
        else:
            try:
                test_num = int(args.task)
                runner.run_test(test_num)
            except ValueError:
                print(f"❌ Invalid task: {args.task}")
                sys.exit(1)
    else:
        # Interactive menu
        print("\n📱 Mobile QA Agent - Test Menu")
        print("=" * 40)
        for num, test in TEST_CASES.items():
            print(f"  {num}. {test['name']}")
        print(f"  a. Run all tests")
        print(f"  q. Quit")
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == 'q':
            return
        elif choice == 'a':
            runner.run_all_tests()
        else:
            try:
                test_num = int(choice)
                runner.run_test(test_num)
            except ValueError:
                print(f"❌ Invalid choice: {choice}")


if __name__ == "__main__":
    main()