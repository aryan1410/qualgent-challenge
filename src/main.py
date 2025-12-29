#!/usr/bin/env python3
"""
Mobile QA Agent - Main Runner
==============================
Run mobile QA tests using Google ADK framework.

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
    )
    from mobile_qa_agent.tools.metrics import MetricsTracker
    from mobile_qa_agent.agent import (
        get_screen_elements,
        tap_at_coordinates,
        tap_element_by_text,
        type_text_input,
        press_enter_key,
        press_back_button,
        ALL_TOOLS,
        get_test_prompt,
        create_test_agent
    )
except ImportError:
    from src.mobile_qa_agent.tools.adb_tools import (
        launch_app,
        clear_app_data,
        check_device_connected,
    )
    from src.mobile_qa_agent.tools.metrics import MetricsTracker
    from src.mobile_qa_agent.agent import (
        get_screen_elements,
        tap_at_coordinates,
        tap_element_by_text,
        type_text_input,
        press_enter_key,
        press_back_button,
        ALL_TOOLS,
        get_test_prompt,
        create_test_agent
    )

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
        "reset_app": True,  # Fresh start needed
        "success_condition": "Screen shows 'Create new note' option (inside vault)",
        "ground_truth_steps": [
            "tap_element: Create a vault",
            "tap_element: Continue without sync",
            "tap_input_field",
            "type_text: InternVault",
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
        "reset_app": False,  # Needs existing vault from Test 1
        "success_condition": "Note exists with title 'Meeting Notes' and content contains 'Daily Standup'",
        "ground_truth_steps": [
            "tap_element: Create new note",
            "tap_input_field: title",
            "clear_and_type: Meeting Notes",
            "tap_element: note body",
            "type_text: Daily Standup"
        ]
    },
    3: {
        "name": "Verify Appearance Icon Color",
        "description": "Navigate to Settings and verify the Appearance tab icon is Red.",
        "expected_result": "FAIL",
        "app_package": "md.obsidian",
        "reset_app": False,  # Needs existing vault
        "success_condition": "Appearance icon is Red colored",
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
        "reset_app": False,  # Needs existing vault
        "success_condition": "Print to PDF option is visible",
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
        "reset_app": False,  # Needs existing vault
        "success_condition": "Both notes 'Project Ideas' and 'Todo List' exist in vault",
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
        "reset_app": False,  # Needs existing notes to search
        "success_condition": "Search results show matching notes",
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
        "reset_app": False,  # Needs existing notes to delete
        "success_condition": "Note is deleted from vault",
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
        "reset_app": False,  # Needs existing vault
        "success_condition": "App is in dark mode",
        "ground_truth_steps": [
            "tap_element: Settings",
            "tap_element: Appearance",
            "tap_element: Dark"
        ]
    },
    9: {
        "name": "Create Vault with New Folder",
        "description": "Create a new vault named 'TestVault' in a new folder named 'TestVault'.",
        "expected_result": "PASS",
        "app_package": "md.obsidian",
        "reset_app": True,  # Fresh start needed - must reset to see Create Vault screen
        "success_condition": "New folder 'TestVault' created and vault setup initiated",
        "ground_truth_steps": [
            "tap_element: Create a vault",
            "tap_element: Continue without sync",
            "tap_input_field",
            "type_text: TestVault",
            "tap_element: Create a vault",
            "tap_element: New folder icon",
            "type_text: TestVault",
            "tap_element: OK"
        ]
    },
    10: {
        "name": "Link Notes",
        "description": "Link two notes together by inserting a link to another note.",
        "expected_result": "PASS",
        "app_package": "md.obsidian",
        "reset_app": False,  # Needs existing notes to link
        "success_condition": "Note contains a link to another note (title and linked note are different)",
        "ground_truth_steps": [
            "tap_element: note body area",
            "tap_element: attach/link button",
            "tap_element: folder",
            "tap_element: other note",
            "verify: link created"
        ]
    }
}


# =============================================================================
# TOOL FUNCTIONS - Now imported from agent.py
# =============================================================================
# Tools are defined in mobile_qa_agent/agent.py:
# - get_screen_elements()
# - tap_at_coordinates(x, y)
# - tap_element_by_text(text)
# - tap_at_coordinates(x, y)
# - type_text_input(x, y, text)
# - press_enter_key()
# - press_back_button()


# =============================================================================
# RUNNER CLASS
# =============================================================================

class MobileQARunner:
    """Runs mobile QA tests using Google ADK."""
    
    def __init__(self, calculate_reward: bool = True, verbose: bool = True):
        self.calculate_reward = calculate_reward
        self.verbose = verbose
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        print("🔍 Checking prerequisites...")
        
        # Check for API keys
        together_key = os.getenv("TOGETHER_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
        
        if together_key:
            print(f"✅ Together API key found")
        elif openai_key:
            print(f"✅ OpenAI API key found")
        elif google_key:
            print(f"✅ Google API key found")
        else:
            print("❌ No API key found. Set TOGETHER_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY")
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
        
        # Only reset app data if test requires it
        if test.get('reset_app', False):
            print(f"   🔄 Resetting app data (fresh start required)")
            clear_app_data(test['app_package'])
            time.sleep(1)
        else:
            print(f"   ♻️ Keeping existing app state (no reset)")
        
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
        """Run test using Google ADK."""
        
        # Determine which model to use based on available API keys
        together_key = os.getenv("TOGETHER_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
        
        if together_key:
            model_name = "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo"
            print(f"🤖 Using Together AI model: {model_name}")
        elif openai_key:
            model_name = "openai/gpt-4o-mini"
            print(f"🤖 Using OpenAI model: {model_name}")
        elif google_key:
            model_name = "gemini-2.0-flash"
            print(f"🤖 Using Gemini model: {model_name}")
        else:
            raise ValueError("No API key found")
        
        # Create the agent using the factory function from agent.py
        test_agent = create_test_agent(
            test_name=test['name'],
            test_description=test['description'],
            success_condition=test.get('success_condition', 'Complete the objective'),
            model_name=model_name
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
        prompt = f"Execute this test: {test['description']}. Start by calling get_screen_elements() to see the current screen elements with their coordinates."
        
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
                        
                        if "TEST PASSED" in response_text.upper() or "PASSED" in response_text.upper():
                            final_result = "PASS"
                            reasoning = response_text
                        elif "TEST FAILED" in response_text.upper() or "FAILED" in response_text.upper():
                            final_result = "FAIL"
                            reasoning = response_text
                
                # Safety limit
                if step_count > 60:
                    print("⚠️ Max events reached")
                    break
                    
        except Exception as e:
            print(f"❌ Agent error: {e}")
            reasoning = str(e)
        
        return final_result, reasoning
    
    # Note: Test instructions are now built in agent.py via get_test_prompt()
    
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