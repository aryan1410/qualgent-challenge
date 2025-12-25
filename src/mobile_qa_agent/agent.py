"""
Mobile QA Agent - Built with Google ADK
========================================
Multi-agent system for automated mobile app testing using Google ADK framework.
"""

import os
import time
import json
from typing import Optional

# Try to import Google ADK (optional - for full agent functionality)
ADK_AVAILABLE = False
try:
    from google.adk.agents import Agent, SequentialAgent
    from google.adk.tools import ToolContext
    ADK_AVAILABLE = True
except ImportError:
    # Create dummy classes for when ADK is not installed
    class Agent:
        def __init__(self, **kwargs):
            self.name = kwargs.get('name', 'agent')
            self.model = kwargs.get('model', 'gemini-2.0-flash')
            self.description = kwargs.get('description', '')
            self.instruction = kwargs.get('instruction', '')
            self.tools = kwargs.get('tools', [])
            self.sub_agents = kwargs.get('sub_agents', [])
    
    class SequentialAgent(Agent):
        pass
    
    class ToolContext:
        pass

# Import our ADB tools
from .tools.adb_tools import (
    take_screenshot,
    tap,
    tap_element,
    tap_input_field,
    type_text,
    clear_and_type,
    press_enter,
    press_back,
    swipe,
    find_clickable_elements,
    find_element_by_text,
    get_ui_hierarchy,
    launch_app,
    clear_app_data
)

from .tools.metrics import MetricsTracker


# =============================================================================
# TOOL DEFINITIONS (wrapped for ADK)
# =============================================================================

def adb_tap_element(element_text: str) -> dict:
    """
    Tap on a UI element by its text label.
    
    Args:
        element_text: The text of the element to tap (e.g., "Create a vault")
    
    Returns:
        dict: Status and result message
    """
    result = tap_element(element_text)
    if "Error" in result:
        return {"status": "error", "message": result}
    return {"status": "success", "message": result}


def adb_tap_coordinates(x: int, y: int) -> dict:
    """
    Tap at specific screen coordinates.
    
    Args:
        x: X coordinate (0-1080 typically)
        y: Y coordinate (0-2400 typically)
    
    Returns:
        dict: Status and result message
    """
    result = tap(x, y)
    return {"status": "success", "message": result}


def adb_tap_input(x: int, y: int) -> dict:
    """
    Tap on an input field (handles stylus popup automatically).
    
    Args:
        x: X coordinate of input field
        y: Y coordinate of input field
    
    Returns:
        dict: Status and result message
    """
    result = tap_input_field(x, y)
    return {"status": "success", "message": result}


def adb_type_text(text: str) -> dict:
    """
    Type text into the currently focused input field.
    
    Args:
        text: The text to type
    
    Returns:
        dict: Status and result message
    """
    result = type_text(text)
    return {"status": "success", "message": result}


def adb_clear_and_type(text: str) -> dict:
    """
    Clear the current input field and type new text.
    Use this when the field has existing text that needs to be replaced.
    
    Args:
        text: The text to type after clearing
    
    Returns:
        dict: Status and result message
    """
    result = clear_and_type(text)
    return {"status": "success", "message": result}


def adb_press_enter() -> dict:
    """
    Press the Enter/Done key to submit or dismiss keyboard.
    
    Returns:
        dict: Status and result message
    """
    result = press_enter()
    return {"status": "success", "message": result}


def adb_press_back() -> dict:
    """
    Press the Android back button.
    
    Returns:
        dict: Status and result message
    """
    result = press_back()
    return {"status": "success", "message": result}


def adb_swipe(start_x: int, start_y: int, end_x: int, end_y: int) -> dict:
    """
    Perform a swipe gesture on the screen.
    
    Args:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
    
    Returns:
        dict: Status and result message
    """
    result = swipe(start_x, start_y, end_x, end_y)
    return {"status": "success", "message": result}


def adb_get_screen_state() -> dict:
    """
    Get the current state of the screen including all UI elements.
    Use this to understand what's on screen before deciding what to do.
    
    Returns:
        dict: Screen state with list of elements and their properties
    """
    elements = find_clickable_elements()
    
    # Format elements for easy reading
    formatted = []
    for elem in elements[:20]:  # Limit to 20 elements
        text = elem.get('text', '') or elem.get('content_desc', '')
        if text:
            formatted.append({
                "text": text,
                "class": elem.get('class', ''),
                "clickable": elem.get('clickable', False),
                "position": (elem.get('center_x', 0), elem.get('center_y', 0))
            })
    
    # Detect screen type
    all_text = ' '.join([e.get('text', '').lower() for e in elements])
    screen_type = "unknown"
    suggested_action = ""
    
    if 'create a vault' in all_text and 'use my existing' in all_text:
        screen_type = "initial_vault_choice"
        suggested_action = "Tap 'Create a vault' to start creating a new vault"
    elif 'vault name' in all_text:
        screen_type = "vault_configuration"
        suggested_action = "Enter vault name in the input field, then tap 'Create a vault'"
    elif 'continue without sync' in all_text:
        screen_type = "sync_setup"
        suggested_action = "Tap 'Continue without sync'"
    elif 'use this folder' in all_text:
        screen_type = "folder_picker"
        suggested_action = "Tap 'USE THIS FOLDER' button at the bottom"
    elif 'allow' in all_text.lower():
        screen_type = "permission_dialog"
        suggested_action = "Tap 'Allow' or 'ALLOW' to grant permission"
    elif 'create new note' in all_text:
        screen_type = "inside_vault"
        suggested_action = "You are inside the vault! Task may be complete."
    elif 'untitled' in all_text:
        screen_type = "note_editing"
        suggested_action = "Tap the title to edit it, then type content"
    
    return {
        "status": "success",
        "screen_type": screen_type,
        "suggested_action": suggested_action,
        "elements": formatted,
        "element_count": len(elements)
    }


def adb_take_screenshot() -> dict:
    """
    Take a screenshot of the current screen.
    
    Returns:
        dict: Status and base64 encoded screenshot
    """
    screenshot = take_screenshot()
    if screenshot.startswith("Error"):
        return {"status": "error", "message": screenshot}
    return {"status": "success", "screenshot_b64": screenshot[:100] + "...(truncated)"}


def mark_test_complete(result: str, reason: str) -> dict:
    """
    Mark the current test as complete.
    
    Args:
        result: "PASS" or "FAIL"
        reason: Explanation of why the test passed or failed
    
    Returns:
        dict: Test completion status
    """
    return {
        "status": "complete",
        "result": result,
        "reason": reason
    }


# =============================================================================
# AGENT DEFINITIONS
# =============================================================================

# Planner Agent - Analyzes screen and decides actions
planner_agent = Agent(
    name="planner_agent",
    model="gemini-2.0-flash",
    description="Analyzes the Android screen and decides what action to take next",
    instruction="""You are a Mobile QA Test Planner Agent. Your job is to:

1. First, call adb_get_screen_state() to see what's on the screen
2. Analyze the screen elements and determine the best action
3. Execute the appropriate action using the available tools

## CRITICAL RULES:

### For Text Input:
When you need to enter text in a field:
1. First tap the input field using adb_tap_element or adb_tap_coordinates
2. Then IMMEDIATELY call adb_clear_and_type with the text (don't skip this!)
3. Then call adb_press_enter to confirm

### For Confirmation Screens:
When you see screens with folders/files and a button like "USE THIS FOLDER":
- DO NOT tap on the folder repeatedly
- Instead, tap the confirmation button (USE THIS FOLDER, OK, ALLOW, etc.)

### For Permission Dialogs:
- Tap "Allow" or "ALLOW" to grant permissions

### Test Completion:
When the test objective is achieved (e.g., you see "Create new note" for vault creation):
- Call mark_test_complete with result="PASS" and explain why

If you get stuck or cannot proceed:
- Call mark_test_complete with result="FAIL" and explain the issue

## Available Actions:
- adb_get_screen_state(): See what's on screen
- adb_tap_element(text): Tap a button/element by its text
- adb_tap_coordinates(x, y): Tap at specific coordinates
- adb_tap_input(x, y): Tap an input field
- adb_type_text(text): Type text
- adb_clear_and_type(text): Clear field and type
- adb_press_enter(): Press enter
- adb_press_back(): Press back
- adb_swipe(start_x, start_y, end_x, end_y): Swipe
- mark_test_complete(result, reason): Complete the test
""",
    tools=[
        adb_get_screen_state,
        adb_tap_element,
        adb_tap_coordinates,
        adb_tap_input,
        adb_type_text,
        adb_clear_and_type,
        adb_press_enter,
        adb_press_back,
        adb_swipe,
        mark_test_complete,
    ],
)


# Supervisor Agent - Evaluates test results
supervisor_agent = Agent(
    name="supervisor_agent",
    model="gemini-2.0-flash",
    description="Evaluates test results and provides final verdict",
    instruction="""You are a QA Test Supervisor Agent. Your job is to:

1. Review the test case objective
2. Analyze what actions were taken
3. Check the final screen state
4. Determine if the test PASSED or FAILED

## Result Types:
- test_passed: Test objective achieved successfully
- test_assertion_failed: App has a bug (wrong behavior detected)
- element_not_found: Required UI element was missing
- execution_error: Test infrastructure issue (not an app bug)

## Output:
Provide a clear verdict with:
- final_result: "PASS" or "FAIL"
- result_type: One of the types above
- reasoning: Clear explanation
- bug_report: If a bug was found, describe it

Always call adb_get_screen_state() first to see the final state.
""",
    tools=[
        adb_get_screen_state,
        adb_take_screenshot,
    ],
)


# Root Agent - Orchestrates the testing process
root_agent = Agent(
    name="mobile_qa_orchestrator",
    model="gemini-2.0-flash",
    description="Orchestrates mobile QA testing with multiple specialized agents",
    instruction="""You are the Mobile QA Test Orchestrator. You coordinate testing of Android apps.

When given a test case:
1. Understand the test objective
2. Use the planner to execute steps
3. Monitor progress and handle issues
4. Report final results

For each test, work step by step:
- First get the screen state
- Decide what action to take
- Execute the action
- Check if objective is achieved
- Repeat until done or stuck

Be systematic and thorough. If something doesn't work, try alternative approaches.
""",
    tools=[
        adb_get_screen_state,
        adb_tap_element,
        adb_tap_coordinates,
        adb_tap_input,
        adb_type_text,
        adb_clear_and_type,
        adb_press_enter,
        adb_press_back,
        adb_swipe,
        mark_test_complete,
    ],
    sub_agents=[planner_agent, supervisor_agent],
)
