"""
Agents Module V3 - With UI Element Detection
=============================================
Uses Android UI Automator to find actual element coordinates.
Much more reliable than vision-based coordinate guessing!
"""

import json
import re
import time
from typing import Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from groq import Groq

from adb_tools import (
    take_screenshot, tap, tap_input_field, tap_element, tap_input_by_label,
    swipe, type_text, press_back, press_enter, wait, launch_app, 
    dismiss_stylus_popup, get_screen_size, get_screen_elements_description, 
    find_element_by_text, get_element_coordinates, find_clickable_elements,
    find_input_field, get_input_field_coordinates
)
from prompts import PLANNER_PROMPT, SUPERVISOR_PROMPT

DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


@dataclass
class ActionResult:
    action_type: str
    action_params: dict
    success: bool
    message: str
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None


@dataclass 
class TestResult:
    test_case: str
    steps_taken: list
    final_result: str
    result_type: str
    reasoning: str
    bug_report: Optional[str] = None
    duration_seconds: float = 0.0


class PlannerAgent:
    """
    Analyzes screenshots and UI elements to decide actions.
    Now uses UI element detection for accurate coordinates!
    """

    def __init__(self, client: Groq, model_name: str = DEFAULT_MODEL):
        self.client = client
        self.model_name = model_name
        self.history = []
        self.screen_width, self.screen_height = get_screen_size()

    def reset(self):
        self.history = []

    def _get_ui_context(self) -> str:
        """Get current UI elements to help the model make decisions."""
        try:
            elements = find_clickable_elements()
            if not elements:
                return "\n[Could not detect UI elements - use visual estimation]\n"
            
            # Detect which screen we're on
            element_texts = [e.get('text', '').lower() for e in elements]
            all_text = ' '.join(element_texts)
            
            screen_type = "unknown"
            priority_action = None
            
            # Check what the last action was
            last_action = self.history[-1] if self.history else None
            last_action_type = last_action.get('action_type') if last_action else None
            
            # If we just tapped an input field, we MUST type text next!
            if last_action_type in ['tap_input', 'tap_input_by_label']:
                return f"""
## ⚠️ INPUT FIELD WAS JUST TAPPED - YOU MUST TYPE TEXT NOW!

Last action: {last_action_type}
Next required action: type_text

You CANNOT tap any buttons until you type the text!

Example:
{{"action_type": "type_text", "action_params": {{"text": "InternVault"}}}}
"""
            
            if 'vault name' in all_text and 'create a vault' in all_text:
                screen_type = "vault_configuration"
                # Check if vault name field has been filled
                input_field = find_input_field()
                if input_field:
                    current_value = input_field.get('text', 'My vault')
                    if current_value == 'My vault' or current_value == '':
                        priority_action = "MUST: 1) tap_input_by_label for 'Vault name', 2) type_text 'InternVault', 3) press_enter, 4) tap 'Create a vault'"
                    else:
                        priority_action = f"Vault name is '{current_value}'. Tap 'Create a vault' button to finish."
            elif 'continue without sync' in all_text:
                screen_type = "sync_setup"
                priority_action = "Tap 'Continue without sync' button"
            elif 'create a vault' in all_text and 'use my existing' in all_text:
                screen_type = "initial_vault_choice"
                priority_action = "Tap 'Create a vault' button"
            
            # Build context
            context = f"\n## SCREEN: {screen_type}\n"
            
            if priority_action:
                context += f"🎯 {priority_action}\n"
            
            # Check for input field
            input_field = find_input_field()
            if input_field:
                x, y = input_field['center_x'], input_field['center_y']
                current_text = input_field.get('text', '[empty]')
                context += f"\n📝 INPUT FIELD at ({x}, {y}) - current value: '{current_text}'\n"
                
                if current_text in ['My vault', '', '[empty]']:
                    context += "   ⚠️ Field needs text! After tapping, you MUST use type_text!\n"
            
            # List buttons
            buttons = []
            for elem in elements[:15]:
                text = elem.get('text') or elem.get('content_desc')
                if text and (elem.get('clickable') or 'button' in elem.get('class', '').lower()):
                    buttons.append(f"  • '{text}'")
            
            if buttons:
                context += "\nBUTTONS:\n" + "\n".join(buttons[:8]) + "\n"
            
            return context
        except Exception as e:
            return f"\n[UI detection error: {e}]\n"

    def _check_for_loop(self) -> Optional[dict]:
        """Check if agent is stuck or oscillating between screens."""
        if len(self.history) < 3:
            return None
        
        last_3 = self.history[-3:]
        
        # Check for repeated actions
        action_strs = [f"{a.get('action_type')}:{a.get('action_params', {})}" for a in last_3]
        if len(set(action_strs)) == 1:
            return {
                "reasoning": "Detected loop - same action repeated 3 times with no progress",
                "action_type": "failed",
                "action_params": {"reason": "Stuck in loop. Need different approach."}
            }
        
        # Check for oscillation (back and forth pattern)
        if len(self.history) >= 4:
            last_4 = self.history[-4:]
            # Check if we're alternating between two actions
            if (last_4[0].get('action_type') == last_4[2].get('action_type') and
                last_4[1].get('action_type') == last_4[3].get('action_type') and
                last_4[0].get('action_type') != last_4[1].get('action_type')):
                return {
                    "reasoning": "Detected oscillation - going back and forth between screens",
                    "action_type": "failed", 
                    "action_params": {"reason": "Stuck oscillating. One action is taking us backwards."}
                }
        
        return None

    def _get_required_next_action(self, test_case: str) -> Optional[dict]:
        """
        Check if a specific action is required based on the last action.
        This enforces the tap_input → type_text → press_enter sequence.
        """
        if not self.history:
            return None
        
        last_action = self.history[-1]
        last_type = last_action.get('action_type', '')
        last_result = last_action.get('result', '')
        
        # If we just tapped an input field, we MUST type text next
        if last_type in ['tap_input_by_label', 'tap_input'] and last_result == 'success':
            # Check what text we need to type based on test case
            text_to_type = None
            if 'internvault' in test_case.lower():
                text_to_type = 'InternVault'
            elif 'meeting notes' in test_case.lower():
                text_to_type = 'Meeting Notes'
            elif 'daily standup' in test_case.lower():
                text_to_type = 'Daily Standup'
            
            if text_to_type:
                print(f"🔄 Auto-forcing type_text after input tap: '{text_to_type}'")
                return {
                    "reasoning": f"Just tapped input field. MUST type '{text_to_type}' now.",
                    "action_type": "type_text",
                    "action_params": {"text": text_to_type}
                }
        
        # If we just typed text, we should press enter to dismiss keyboard
        if last_type == 'type_text' and last_result == 'success':
            print("🔄 Auto-forcing press_enter after type_text")
            return {
                "reasoning": "Just typed text. Pressing enter to dismiss keyboard.",
                "action_type": "press_enter",
                "action_params": {}
            }
        
        return None

    def plan_next_action(self, test_case: str, screenshot_b64: str) -> dict:
        """Analyze screenshot + UI elements and decide next action."""
        
        # Check for loops
        loop_result = self._check_for_loop()
        if loop_result:
            return loop_result
        
        # CHECK FOR REQUIRED ACTIONS FIRST (state machine enforcement)
        required_action = self._get_required_next_action(test_case)
        if required_action:
            return required_action
        
        # Get actual UI elements
        ui_context = self._get_ui_context()
        
        # Build history context
        history_text = ""
        if self.history:
            history_text = "\n## PREVIOUS ACTIONS:\n"
            for i, action in enumerate(self.history[-5:], 1):
                atype = action.get('action_type', '?')
                params = action.get('action_params', {})
                result = action.get('result', '?')
                history_text += f"{i}. {atype}({params}) → {result}\n"

        prompt = f"""{PLANNER_PROMPT}

{ui_context}

## CURRENT TEST CASE
{test_case}

{history_text}

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1024,
                temperature=0.1
            )

            response_text = response.choices[0].message.content.strip()

            # Extract JSON
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                response_text = json_match.group(1).strip()
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                response_text = response_text[json_start:json_end]

            action = json.loads(response_text)

            if "action_type" not in action:
                return {
                    "reasoning": "Invalid response",
                    "action_type": "failed",
                    "action_params": {"reason": "Missing action_type"}
                }

            return action

        except json.JSONDecodeError as e:
            return {
                "reasoning": f"JSON error: {e}",
                "action_type": "failed",
                "action_params": {"reason": "Could not parse response"}
            }
        except Exception as e:
            if "429" in str(e):
                print("⚠️  Rate limited. Waiting...")
                time.sleep(60)
                return {"reasoning": "Rate limited", "action_type": "wait", "action_params": {"seconds": 2}}
            return {
                "reasoning": f"Error: {e}",
                "action_type": "failed",
                "action_params": {"reason": str(e)}
            }

    def record_action(self, action: dict, result: str):
        self.history.append({**action, "result": result})


class ExecutorAgent:
    """Executes actions including the new tap_element action."""

    def __init__(self):
        self.screen_width, self.screen_height = get_screen_size()

    def execute(self, action_type: str, action_params: dict) -> ActionResult:
        screenshot_before = take_screenshot()
        message = ""
        success = True

        try:
            if action_type == "tap":
                x = action_params.get("x", 540)
                y = action_params.get("y", 1000)
                message = tap(x, y)
                success = "Error" not in message

            elif action_type == "tap_element":
                # NEW: Tap by element text - uses UI detection!
                text = action_params.get("text", "")
                if not text:
                    message = "Error: No text provided for tap_element"
                    success = False
                else:
                    message = tap_element(text)
                    success = "Error" not in message

            elif action_type == "tap_input":
                x = action_params.get("x", 540)
                y = action_params.get("y", 600)
                
                # SMART FIX: If coordinates seem wrong (too high), find actual input field
                if y < 550:  # Likely tapping a label, not the field
                    print(f"⚠️  Coordinates ({x}, {y}) seem too high for input field. Auto-detecting...")
                    field = find_input_field()
                    if field:
                        x = field['center_x']
                        y = field['center_y']
                        print(f"✓ Found actual input field at ({x}, {y})")
                
                message = tap_input_field(x, y)
                success = "Error" not in message

            elif action_type == "tap_input_by_label":
                # NEW: Find input field by its label and tap it
                label = action_params.get("label", "")
                if not label:
                    message = "Error: No label provided"
                    success = False
                else:
                    message = tap_input_by_label(label)
                    success = "Error" not in message

            elif action_type == "swipe":
                message = swipe(
                    action_params.get("start_x", 540),
                    action_params.get("start_y", 1500),
                    action_params.get("end_x", 540),
                    action_params.get("end_y", 500),
                    action_params.get("duration_ms", 300)
                )
                success = "Error" not in message

            elif action_type == "type_text":
                text = action_params.get("text", "")
                message = type_text(text)
                success = "Error" not in message

            elif action_type == "press_back":
                message = press_back()
                success = "Error" not in message

            elif action_type == "press_enter":
                message = press_enter()
                success = "Error" not in message

            elif action_type == "wait":
                seconds = action_params.get("seconds", 1.0)
                message = wait(seconds)
                success = True

            elif action_type in ["done", "failed"]:
                message = action_params.get("reason", action_params.get("result", "Completed"))
                success = True

            else:
                message = f"Unknown action type: {action_type}"
                success = False

        except Exception as e:
            message = f"Execution error: {str(e)}"
            success = False

        wait(0.5)
        screenshot_after = take_screenshot()

        return ActionResult(
            action_type=action_type,
            action_params=action_params,
            success=success,
            message=message,
            screenshot_before=screenshot_before,
            screenshot_after=screenshot_after
        )


class SupervisorAgent:
    """Evaluates test results."""

    def __init__(self, client: Groq, model_name: str = DEFAULT_MODEL):
        self.client = client
        self.model_name = model_name

    def evaluate_test(self, test_case: str, action_history: list, 
                      final_screenshot_b64: str) -> TestResult:
        steps_summary = []
        for i, action in enumerate(action_history, 1):
            steps_summary.append({
                "step": i,
                "action": action.get("action_type"),
                "params": action.get("action_params", {}),
                "result": action.get("result", "unknown")
            })

        prompt = f"""{SUPERVISOR_PROMPT}

## TEST CASE
{test_case}

## ACTIONS TAKEN
{json.dumps(steps_summary, indent=2)}

Analyze the final screenshot and determine if the test passed or failed.
Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{final_screenshot_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1024,
                temperature=0.1
            )

            response_text = response.choices[0].message.content.strip()
            
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                response_text = json_match.group(1).strip()
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                response_text = response_text[json_start:json_end]

            result = json.loads(response_text)

            return TestResult(
                test_case=test_case,
                steps_taken=steps_summary,
                final_result=result.get("final_result", "FAIL"),
                result_type=result.get("result_type", "execution_error"),
                reasoning=result.get("reasoning", "No reasoning"),
                bug_report=result.get("bug_report")
            )

        except Exception as e:
            return TestResult(
                test_case=test_case,
                steps_taken=steps_summary,
                final_result="FAIL",
                result_type="execution_error",
                reasoning=f"Supervisor error: {str(e)}",
                bug_report=None
            )


class MobileQAOrchestrator:
    """Coordinates all agents."""

    def __init__(self, api_key: str, model_name: str = DEFAULT_MODEL):
        self.client = Groq(api_key=api_key)
        self.model_name = model_name
        
        print(f"🤖 Mobile QA Agent v3 - With UI Detection")
        print(f"   Model: {model_name}")
        
        self.planner = PlannerAgent(self.client, model_name)
        self.executor = ExecutorAgent()
        self.supervisor = SupervisorAgent(self.client, model_name)
        self.max_steps = 20

    def run_test(self, test_case: str, verbose: bool = True) -> TestResult:
        start_time = datetime.now()

        if verbose:
            print(f"\n{'='*60}")
            print(f"📋 TEST: {test_case}")
            print(f"{'='*60}\n")

        self.planner.reset()
        step_count = 0

        while step_count < self.max_steps:
            step_count += 1

            if verbose:
                print(f"\n--- Step {step_count}/{self.max_steps} ---")

            screenshot = take_screenshot()
            if screenshot.startswith("Error"):
                if verbose:
                    print(f"❌ Screenshot error: {screenshot}")
                break

            if verbose:
                print("🔍 Planner analyzing (with UI detection)...")

            if step_count > 1:
                time.sleep(1)

            action = self.planner.plan_next_action(test_case, screenshot)

            # SAFEGUARD: If we just tapped input field, next action MUST be type_text
            if self.planner.history:
                last_action = self.planner.history[-1]
                last_type = last_action.get('action_type')
                
                if last_type in ['tap_input', 'tap_input_by_label']:
                    current_action = action.get('action_type')
                    if current_action != 'type_text':
                        if verbose:
                            print(f"⚠️  OVERRIDE: Must type text after tapping input! (was: {current_action})")
                        # Force type_text - extract text from test case
                        text_to_type = None
                        test_lower = test_case.lower()
                        if 'internvault' in test_lower:
                            text_to_type = "InternVault"
                        elif 'meeting notes' in test_lower:
                            text_to_type = "Meeting Notes"
                        elif 'daily standup' in test_lower:
                            text_to_type = "Daily Standup"
                        
                        if text_to_type:
                            action = {
                                "reasoning": f"OVERRIDE: Must type '{text_to_type}' after tapping input",
                                "action_type": "type_text",
                                "action_params": {"text": text_to_type}
                            }

            if verbose:
                reasoning = action.get('reasoning', 'N/A')[:120]
                print(f"💭 {reasoning}...")
                print(f"🎯 {action['action_type']} → {action.get('action_params', {})}")

            if action["action_type"] == "done":
                self.planner.record_action(action, "DONE")
                if verbose:
                    print(f"\n✅ Test completed: {action.get('action_params', {})}")
                break

            if action["action_type"] == "failed":
                self.planner.record_action(action, "FAILED")
                if verbose:
                    print(f"\n❌ Failed: {action.get('action_params', {}).get('reason')}")
                break

            result = self.executor.execute(
                action["action_type"],
                action.get("action_params", {})
            )

            if verbose:
                icon = "✓" if result.success else "✗"
                print(f"📱 Executor: {icon} {result.message}")

            self.planner.record_action(action, "success" if result.success else "failed")

        final_screenshot = take_screenshot()

        if verbose:
            print("\n" + "-"*40)
            print("🔎 Supervisor evaluating...")

        time.sleep(1)

        test_result = self.supervisor.evaluate_test(
            test_case,
            self.planner.history,
            final_screenshot
        )

        test_result.duration_seconds = (datetime.now() - start_time).total_seconds()

        if verbose:
            icon = "✅" if test_result.final_result == "PASS" else "❌"
            print(f"\n{icon} RESULT: {test_result.final_result}")
            print(f"📋 Type: {test_result.result_type}")
            print(f"💬 {test_result.reasoning[:200]}...")
            if test_result.bug_report:
                print(f"🐛 Bug: {test_result.bug_report}")
            print(f"⏱️  {test_result.duration_seconds:.1f}s")

        return test_result

    def run_test_suite(self, test_cases: list, verbose: bool = True) -> list:
        results = []

        for i, test_case in enumerate(test_cases, 1):
            if verbose:
                print(f"\n\n{'#'*60}")
                print(f"TEST {i}/{len(test_cases)}")
                print(f"{'#'*60}")

            result = self.run_test(test_case, verbose)
            results.append(result)

            press_back()
            wait(1)

            if i < len(test_cases):
                if verbose:
                    print("\n⏳ Waiting 5s...")
                time.sleep(5)

        if verbose:
            print(f"\n\n{'='*60}")
            print("📊 SUMMARY")
            print(f"{'='*60}")

            passed = sum(1 for r in results if r.final_result == "PASS")
            
            for i, r in enumerate(results, 1):
                icon = "✅" if r.final_result == "PASS" else "❌"
                print(f"  {icon} Test {i}: {r.final_result} ({r.result_type})")

            print(f"\n📈 {passed}/{len(results)} passed")

        return results