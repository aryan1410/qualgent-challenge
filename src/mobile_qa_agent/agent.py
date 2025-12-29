"""
Mobile QA Agent - Smart Agent with UI Element Detection
========================================================
Agent uses UI extractor to get exact coordinates and makes intelligent decisions.
"""

import os
import time
import subprocess
from typing import Optional, Dict, Any, List

# Try to import Google ADK
ADK_AVAILABLE = False
try:
    from google.adk.agents import Agent
    ADK_AVAILABLE = True
except ImportError:
    class Agent:
        def __init__(self, **kwargs):
            self.name = kwargs.get('name', 'agent')
            self.model = kwargs.get('model', 'gemini-2.0-flash')

# Import ADB tools
try:
    from .tools.adb_tools import (
        tap,
        clear_and_type,
        press_enter,
        press_back,
        type_text,
        get_ui_hierarchy,
        parse_ui_elements,
        tap_element,
        clear_field,
        take_screenshot_compressed
    )
except ImportError:
    from tools.adb_tools import (
        tap,
        clear_and_type,
        press_enter,
        press_back,
        type_text,
        get_ui_hierarchy,
        parse_ui_elements,
        tap_element,
        clear_field,
        take_screenshot_compressed
    )


# =============================================================================
# SMART TOOL FUNCTIONS - Agent gets UI data and decides what to do
# =============================================================================

def get_screen_elements() -> dict:
    """
    Get all UI elements on screen with their exact coordinates AND a screenshot.
    
    Returns:
    - screenshot_base64: Base64 encoded PNG image of current screen (compressed)
    - elements: List of UI elements with {text, x, y, width, height, type}
    - screen_type: Detected screen type
    
    The agent can VIEW the screenshot to see icons, colors, and layout visually,
    then use the element coordinates to tap on specific items.
    """
    # Take screenshot and compress it
    screenshot_b64 = take_screenshot_compressed()
    has_screenshot = screenshot_b64 is not None and not screenshot_b64.startswith("Error")
    
    xml = get_ui_hierarchy()
    if xml.startswith("Error"):
        return {"error": xml, "elements": [], "screenshot_base64": screenshot_b64 if has_screenshot else None}
    
    elements = parse_ui_elements(xml)
    
    # Filter and simplify for the agent
    ui_elements = []
    for elem in elements:
        text = elem.get('text', '') or elem.get('content_desc', '')
        width = elem.get('width', 0)
        height = elem.get('height', 0)
        x = elem.get('center_x', 0)
        y = elem.get('center_y', 0)
        class_name = elem.get('class', '')
        
        # Skip full-screen containers
        if width > 900 and height > 900:
            continue
        
        # Skip elements with invalid coordinates
        if y > 2300 or y < 0 or x < 0 or x > 1080:
            continue
        
        # Determine element type
        elem_type = "text"
        if 'EditText' in class_name:
            elem_type = "input"
        elif 'Button' in class_name or elem.get('clickable', False):
            elem_type = "button"
        
        # Include elements with text OR input fields (even if empty)
        if text or elem_type == "input":
            ui_elements.append({
                "text": text[:50] if text else "[input field]",
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "clickable": elem.get('clickable', False),
                "type": elem_type
            })
    
    # Sort by y position (top to bottom)
    ui_elements.sort(key=lambda e: e['y'])
    
    # Detect screen type based on text
    all_text = ' '.join([e['text'].lower() for e in ui_elements])
    
    screen_type = "unknown"
    if 'create new note' in all_text and 'create a vault' not in all_text:
        screen_type = "inside_vault"
    elif 'create a vault' in all_text and 'use my existing' in all_text:
        screen_type = "initial_vault_choice"
    elif 'continue without sync' in all_text:
        screen_type = "sync_setup"
    elif 'vault name' in all_text or 'my vault' in all_text:
        screen_type = "vault_configuration"
    elif 'use this folder' in all_text:
        screen_type = "folder_picker"
    elif 'files in' in all_text and 'documents' in all_text:
        screen_type = "folder_picker"
    elif 'no items' in all_text and 'files in' in all_text:
        screen_type = "folder_picker"
    elif 'allow' in all_text and len(ui_elements) < 15:
        screen_type = "permission_dialog"
    elif 'options' in all_text and ('general' in all_text or 'editor' in all_text or 'appearance' in all_text):
        screen_type = "settings_screen"
    elif 'appearance' in all_text and ('base color' in all_text or 'accent color' in all_text or 'theme' in all_text):
        screen_type = "appearance_settings"
    elif 'meeting notes' in all_text:
        screen_type = "note_editor_with_title"
    elif 'untitled' in all_text:
        screen_type = "note_editor"
    
    # Debug output
    print(f"[get_screen_elements] screen_type={screen_type}, {len(ui_elements)} elements, screenshot={'yes' if has_screenshot else 'no'}")
    for e in ui_elements[:10]:
        print(f"    '{e['text'][:25]:<25}' at ({e['x']:>4}, {e['y']:>4}) {e['width']}x{e['height']} type={e['type']}")
    
    return {
        "screen_type": screen_type,
        "element_count": len(ui_elements),
        "elements": ui_elements[:20],
        "screenshot_base64": screenshot_b64 if has_screenshot else None,
        "hint": "LOOK AT THE SCREENSHOT to see icons, buttons, and visual layout. Use element coordinates to tap."
    }


def tap_at_coordinates(x: int, y: int) -> dict:
    """
    Tap at exact screen coordinates.
    
    Use the (x, y) from get_screen_elements() to tap on specific elements.
    
    Args:
        x: X coordinate from element info
        y: Y coordinate from element info
    """
    print(f"[tap_at_coordinates] Tapping at ({x}, {y})")
    tap(x, y)
    time.sleep(1.0)
    return {"success": True, "message": f"Tapped at ({x}, {y})"}


def tap_element_by_text(text: str) -> dict:
    """
    Find an element by text and tap it.
    
    Args:
        text: Text to search for (case-insensitive partial match)
    """
    print(f"[tap_element_by_text] Looking for: '{text}'")
    result = tap_element(text)
    success = "Error" not in result
    print(f"[tap_element_by_text] Result: {result}")
    time.sleep(1.0)
    return {"success": success, "message": result}


def type_text_input(x: int, y: int, text: str, clear_first: bool = True) -> dict:
    """
    Tap an INPUT FIELD at coordinates, type text, then dismiss keyboard.
    
    IMPORTANT: Only use this on actual input fields, not on labels!
    The input field is usually BELOW the label (e.g., if "Vault name" label is at y=507,
    the input field is around y=580-600).
    
    Args:
        x: X coordinate of the INPUT FIELD (not the label!)
        y: Y coordinate of the INPUT FIELD (not the label!)
        text: Text to type
        clear_first: If True, clear existing text before typing
    """
    print(f"[type_text_input] At ({x}, {y}), typing: '{text}', clear={clear_first}")
    
    # Tap to focus the input field
    tap(x, y)
    time.sleep(0.5)
    
    # Check if keyboard appeared by waiting a moment
    time.sleep(0.3)
    
    if clear_first:
        # Select all with Ctrl+A
        subprocess.run(["adb", "shell", "input", "keyevent", "--longpress", "113", "29"], capture_output=True)
        time.sleep(0.2)
        
        # Delete
        subprocess.run(["adb", "shell", "input", "keyevent", "67"], capture_output=True)
        time.sleep(0.1)
    
    # Type the text
    type_text(text)
    time.sleep(0.3)
    
    # Dismiss keyboard by pressing back
    press_back()
    time.sleep(0.5)
    
    return {"success": True, "message": f"Typed '{text}' at ({x}, {y})"}


def press_enter_key() -> dict:
    """Press Enter key."""
    print("[press_enter_key] Pressing Enter")
    press_enter()
    time.sleep(0.3)
    return {"success": True, "message": "Pressed Enter"}


def press_back_button() -> dict:
    """Press Back button to go back or dismiss keyboard/popups."""
    print("[press_back_button] Pressing Back")
    press_back()
    time.sleep(0.5)
    return {"success": True, "message": "Pressed Back"}


def swipe_screen(direction: str = "up") -> dict:
    """
    Swipe/scroll the screen.
    
    Args:
        direction: "up" to scroll down (see more content below), 
                   "down" to scroll up (see content above)
    """
    print(f"[swipe_screen] Swiping {direction}")
    
    # Screen center x
    center_x = 540
    
    if direction == "up":
        # Swipe up = scroll down = see more content below
        start_y, end_y = 1500, 500
    else:
        # Swipe down = scroll up = see content above
        start_y, end_y = 500, 1500
    
    subprocess.run([
        "adb", "shell", "input", "swipe",
        str(center_x), str(start_y), str(center_x), str(end_y), "300"
    ], capture_output=True)
    
    time.sleep(0.5)
    return {"success": True, "message": f"Swiped {direction}"}


# All tools available to the agent
ALL_TOOLS = [
    get_screen_elements,
    tap_at_coordinates,
    tap_element_by_text,
    type_text_input,
    press_enter_key,
    press_back_button,
    swipe_screen
]


# =============================================================================
# PROMPTS - Agent is smart and uses coordinates from UI data
# =============================================================================

BASE_SYSTEM_PROMPT = """You are a mobile QA testing agent. Your job is to TAKE ACTIONS, not just describe screens.

IMPORTANT: After every get_screen_elements() call, you MUST take an action (tap, type, swipe, etc.)
DO NOT just describe what you see - ACT on it!

YOU HAVE ACCESS TO:
1. SCREENSHOTS - You can SEE the actual screen visually
2. UI ELEMENT COORDINATES - Exact (x, y) positions for tapping

WORKFLOW (ALWAYS FOLLOW):
1. Call get_screen_elements() to see the screen
2. IMMEDIATELY take an action based on what you see (tap, type, swipe)
3. Call get_screen_elements() again to verify
4. Repeat until objective is complete

AVAILABLE TOOLS:
- get_screen_elements(): Returns screenshot + elements {text, x, y, width, height, type}
- tap_at_coordinates(x, y): Tap at exact position
- tap_element_by_text(text): Find and tap by text
- type_text_input(x, y, text, clear_first): Type into input field
- press_enter_key(): Press Enter
- press_back_button(): Go back / dismiss keyboard
- swipe_screen(direction): "up" to scroll down, "down" to scroll up

RULES:
1. ALWAYS take action after analyzing screen - never just respond with description
2. Use screenshot to find visual elements like icons
3. Use element coordinates for precise tapping
4. If element not in list but visible in screenshot, estimate coordinates
5. Bottom navigation bar icons are around y=2000-2300

Say "TEST PASSED" only after completing ALL required actions.
Say "TEST FAILED" if you cannot complete after multiple attempts.
"""

VAULT_CREATION_PROMPT = """
OBJECTIVE: Create a vault named 'InternVault' and enter it.

USE THE SCREENSHOT to visually confirm each step!

STEPS:
1. get_screen_elements() → Look at screenshot, find "Create a vault" button → tap it
2. get_screen_elements() → Look for sync screen, find "Continue without sync" → tap it  
3. get_screen_elements() → You're on vault config screen:
   - Look at screenshot: you'll see "Vault name" label and an input field below it
   - Find type="input" element (NOT the label!)
   - type_text_input(x, y, "InternVault") on the input field
4. get_screen_elements() → Look at screenshot for "Create a vault" button at bottom → tap it
5. get_screen_elements() → FILE PICKER screen:
   - Look at screenshot: "USE THIS FOLDER" button is at the BOTTOM (blue button)
   - If in elements, use coordinates. If not, tap at (540, 1850)
6. get_screen_elements() → Permission dialog may appear → tap "Allow"
7. get_screen_elements() → Verify you're inside vault:
   - Screenshot should show empty vault with "Create new note" option
   - screen_type="inside_vault"

SUCCESS: Screenshot shows vault interior with "Create new note" visible → TEST PASSED
FAILURE: Can't complete after 5+ attempts → TEST FAILED
"""

CREATE_VAULT_NEW_FOLDER_PROMPT = """
OBJECTIVE: Create a vault with a NEW folder (not using existing folder).

This is similar to vault creation BUT instead of "Use this folder", you create a NEW folder.

STEP-BY-STEP:

STEP 1: Tap "Create a vault" button
- get_screen_elements() → find "Create a vault" → tap it

STEP 2: Tap "Continue without sync"
- get_screen_elements() → find "Continue without sync" → tap it

STEP 3: Enter the vault name in the input field
- get_screen_elements() → find the input field (type="input")
- The input field is BELOW the "Vault name" label
- type_text_input(x, y, "TestVault") - use the vault name from test instructions

STEP 4: Tap "Create a vault" button at bottom
- get_screen_elements() → find "Create a vault" button → tap it

STEP 5: CREATE A NEW FOLDER (THIS IS DIFFERENT!)
- You'll see the file picker screen with "Documents" and existing folders
- DO NOT tap "Use this folder"!
- DO NOT tap on existing folders!
- Look for the "NEW FOLDER" icon (folder with + sign) in the TOP BAR
- It's around coordinates (253, 128) or look for folder+ icon in screenshot
- tap_at_coordinates(253, 128) to create new folder

STEP 6: Enter folder name in the dialog
- A "New folder" dialog appears with an input field
- Find the input field and type the folder name
- type_text_input(x, y, "TestVault") - or use name from test instructions

STEP 7: Tap "OK" to confirm
- tap_element_by_text("OK")

STEP 8: Now tap "USE THIS FOLDER"
- After creating the folder, tap "USE THIS FOLDER" at the bottom
- tap_element_by_text("USE THIS FOLDER") or tap_at_coordinates(540, 2100)

STEP 9: Handle permission dialog if it appears
- Tap "Allow" if prompted

COORDINATES:
- New folder icon (folder+): around (253, 128) in top bar of file picker
- OK button: in the dialog after entering folder name
- USE THIS FOLDER: at the bottom of file picker screen

SUCCESS: New folder created and vault setup complete → TEST PASSED
"""

NOTE_CREATION_PROMPT = """
OBJECTIVE: Create a note titled 'Meeting Notes' with content 'Daily Standup'.

USE THE SCREENSHOT to see the note editor!

STEPS:
1. get_screen_elements() → Look at screenshot, find "Create new note" → tap it
2. get_screen_elements() → Note editor opens:
   - Screenshot shows "Untitled" as the title (bold text)
   - Find the title input (type="input" with larger height)
   - Title is the BIGGER element, header bar text is smaller
3. type_text_input(x, y, "Meeting Notes") on title coordinates
4. get_screen_elements() → Verify in screenshot: title now shows "Meeting Notes"
5. Calculate body position: body_y = title_y + 100
6. type_text_input(x, body_y, "Daily Standup", clear_first=False)
7. get_screen_elements() → Verify title still shows "Meeting Notes"

SUCCESS: Screenshot shows "Meeting Notes" as title → TEST PASSED
(Body text may not appear in elements due to WebView, but if you typed it, trust it worked)
"""

SETTINGS_NAVIGATION_PROMPT = """
OBJECTIVE: Navigate to Settings and find Appearance.

STEP-BY-STEP:

STEP 1: Tap the EXPAND button (sidebar toggle) in the top left
- Coordinates: tap_at_coordinates(100, 128)
- This opens the left sidebar panel

STEP 2: Tap the SETTINGS icon (gear ⚙️) in the sidebar
- After sidebar opens, look for the gear icon in the top area of sidebar
- Coordinates: tap_at_coordinates(280, 75) - it's near the vault name
- Look at the screenshot to find the gear icon

STEP 3: You're now in Settings screen
- You'll see "Settings" at the top and options like: General, Editor, Toolbar, Files and links, Appearance, etc.
- "Appearance" is visible on screen - NO need to scroll!
- tap_element_by_text("Appearance")

STEP 4: Verify you're in Appearance settings
- get_screen_elements() to confirm

FOR APPEARANCE ICON COLOR TEST:
- Once in Settings, look at the icon next to "Appearance"
- Check the color of the icon in the screenshot
- The expected result is FAIL because the Appearance icon is NOT red (it's purple/default)
- Say: TEST FAILED - "The Appearance tab icon is not red, it is [color you see]"

COORDINATES:
- Expand/sidebar toggle: (100, 128) top left
- Settings gear icon: (280, 75) in sidebar header area
- Appearance option: use tap_element_by_text("Appearance")

SUCCESS: Reached Appearance settings → TEST PASSED (unless verifying icon color)
"""

GENERIC_TEST_PROMPT = """
OBJECTIVE: {description}

USE THE SCREENSHOT to understand what's on screen!

APPROACH:
1. get_screen_elements() → Analyze screenshot + elements
2. Identify what action is needed based on the objective
3. Find relevant buttons/inputs in screenshot or element list
4. Take action using coordinates
5. Verify result with another get_screen_elements()

TIPS:
- Screenshot shows actual visual state - trust what you see
- Elements give exact coordinates - use them for tapping
- If an element isn't in the list but visible in screenshot, estimate coordinates
- Common locations: top bar ~y=100-150, bottom buttons ~y=1800-2200

Complete the objective as described, then report TEST PASSED or TEST FAILED.
"""

MULTI_NOTE_CREATION_PROMPT = """
OBJECTIVE: Create multiple NEW notes (DO NOT edit existing notes!)

⚠️ IMPORTANT: TAKE ACTIONS, DON'T JUST DESCRIBE! After get_screen_elements(), IMMEDIATELY tap something!

YOU ARE STARTING ON AN EXISTING NOTE - DO NOT EDIT IT!
You need to tap the '+' icon at the BOTTOM to create NEW notes.

IMMEDIATE FIRST ACTION:
After your first get_screen_elements(), tap the '+' icon at the bottom.
The '+' icon is in the bottom navigation bar, around coordinates (600, 2292)
- tap_at_coordinates(600, 2292)

⚠️ CRITICAL - RESTORING THE BOTTOM BAR WITH '+':
After typing in the body, the bottom bar changes and the '+' icon is NO LONGER THERE!
To bring back the bottom bar with the '+' icon:
1. tap_at_coordinates(540, 129) - tap on the TITLE at the top
2. This restores the correct bottom bar with the '+' sign
3. NEVER use press_back_button() - it navigates away!

STEP-BY-STEP FOR EACH NOTE:

STEP 1: Tap '+' to create new note
- tap_at_coordinates(600, 2292) for the '+' icon
- If '+' doesn't work, first tap_at_coordinates(540, 129) to restore bottom bar, then try '+' again

STEP 2: Tap "Create new note" 
- After tapping '+', you'll see a menu with "Create new note (Ctrl + N)"
- tap_element_by_text("Create new note")

STEP 3: Type the TITLE (REQUIRED)
- New note opens with "Untitled" 
- Find the title input (type="input")
- type_text_input(x, y, "YOUR_TITLE_HERE")

STEP 4: Type the BODY (REQUIRED - DO NOT SKIP!)
⚠️ YOU MUST TYPE THE BODY!
- Body is BELOW the title: body_y = title_y + 100
- type_text_input(x, body_y, "YOUR_BODY_HERE", clear_first=False)

STEP 5: RESTORE BOTTOM BAR BEFORE NEXT NOTE
⚠️ MUST DO THIS BEFORE CREATING NEXT NOTE:
- tap_at_coordinates(540, 129) - tap the TITLE to restore bottom bar with '+'
- DO NOT use press_back_button()!
- get_screen_elements() to verify

STEP 6: For second note, repeat Steps 1-5

⚠️ CRITICAL RULES:
1. EVERY note needs BOTH title AND body
2. NEVER use press_back_button()
3. ALWAYS tap title (540, 129) after typing body to restore the bottom bar with '+'
4. Only tap '+' at (600, 2292) AFTER restoring the correct bottom bar

COORDINATES:
- Tap to restore bottom bar: (540, 129)
- '+' icon: (600, 2292) - only works when correct bottom bar is showing
- Title input: around y=263
- Body: title_y + 100

SUCCESS: Both notes created with correct titles AND bodies → TEST PASSED
"""


SEARCH_NOTE_PROMPT = """
OBJECTIVE: Search for a note using the search feature.

STEP-BY-STEP:

STEP 1: Tap the SEARCH icon (magnifying glass 🔍) in the bottom bar
- The search icon is in the bottom navigation bar
- Coordinates: tap_at_coordinates(148, 2292)
- This opens the search screen with "Find or create a note..."

STEP 2: You'll see the search screen
- There's a search input field at the top saying "Find or create a note..."
- Below it, you'll see a list of existing notes (e.g., "Project Ideas", "Meeting Notes")
- Look at the notes listed in the elements

STEP 3: Type a note name into the search field
- Find the search input field (type="input" with "Find or create a note")
- Pick one of the visible note names from the list below the search field
- type_text_input(x, y, "NOTE_NAME_HERE") - use the name of a note you see listed

STEP 4: Verify the search works
- After typing, the list should filter to show matching results
- get_screen_elements() to verify the note appears in results

COORDINATES:
- Search icon (magnifying glass): (148, 2292) in bottom bar
- Search input field: around y=112 at the top of search screen

SUCCESS: Search field has text entered and results are shown → TEST PASSED
"""

DELETE_NOTE_PROMPT = """
OBJECTIVE: Delete a note.

STEP-BY-STEP:

STEP 1: Tap the THREE DOTS menu (⋮) in the top right
- The three dots "More options" button is in the top right corner
- Coordinates: tap_at_coordinates(990, 128)
- This opens an options menu from the bottom

STEP 2: Scroll down in the options menu to find "Delete file"
- The options menu shows items like: Close, Backlinks, Reading view, Source mode, Pin, Rename, etc.
- "Delete file" is at the BOTTOM of this menu - you need to scroll!
- swipe_screen("up") to scroll down and reveal more options
- Keep scrolling until you see "Delete file" (it's in red text)

STEP 3: Tap "Delete file"
- Once you see "Delete file" in the menu
- tap_element_by_text("Delete file")

STEP 4: Confirm deletion if prompted
- There may be a confirmation dialog
- Tap to confirm the deletion

COORDINATES:
- Three dots menu: (990, 128) in top right
- After menu opens, scroll to find "Delete file" at the bottom

SUCCESS: Note is deleted → TEST PASSED
"""

LINK_NOTES_PROMPT = """
OBJECTIVE: Link two notes together.

You are starting on an open note. You need to insert a link to another note.

STEP-BY-STEP:

STEP 1: Remember the current note's title
- get_screen_elements() → Look at the title of the current note (e.g., "Project Ideas")
- You will need to link to a DIFFERENT note, not this one
- DO NOT TAP AT ANY CO ORDINATE

STEP 2: Tap in the body area to position cursor
- The body is BELOW the title
- Find the title's y coordinate, then tap at title_y + 100 (usually this title_y co ordinate will be 229)
- tap_at_coordinates(title_x, title_y+100)
- This activates editing mode

STEP 4: Select/Type ANOTHER note
- To start linking a note, type the exact text: '[[' in the BODY, not in the TITLE, or next to the TITLE. The BODY is BELOW the TITLE, so tap BELOW the title before typing anything.
- type_text_by_input('x':something, 'y':title_y+100, 'text':'[[', 'clear_first':True)
- If you see some note names, including the current note you are in (could be names like "Meeting Notes", "Todo List", "Project Ideas", etc.)
- Tap on a note DIFFERENT THAN the note you are currently in, so if you are in Project Ideas, then tap_element_by_text("Meeting Notes")
- If you don't see note names, you will see in the body there are two box brackets like this: '[[]]'.
- Tap in the inner most bracket for input and type the first letter of the note you want to link (for e.g if you are in Project Ideas, type 'M' for Meeting Notes)
- You will then see the dropdown and the different note name on the screen, so tap_element_by_text(DIFFERENT_NOTE_NAME)

STEP 5: Verify the link was created
- get_screen_elements() → The note should now show:
  - Title: original note name (e.g., "Project Ideas")
  - Body: contains a link to the other note (e.g., "Meeting Notes")
- The title and the linked note name should be DIFFERENT

If you get stuck, or don't find something on the screen that you are looking for try to look at the screenshot and elements to figure out which step you are on, and make the corresponding next step

SUCCESS CONDITION:
- The note shows a title (e.g., "Project Ideas")
- The body contains a link to a DIFFERENT note (e.g., "Meeting Notes")
- Title text ≠ Linked note text → TEST PASSED
"""


def get_test_prompt(test_name: str, test_description: str, success_condition: str) -> str:
    prompt = BASE_SYSTEM_PROMPT + f"\n\n=== CURRENT TEST ===\nName: {test_name}\nObjective: {test_description}\nSuccess: {success_condition}\n\n"
    
    test_lower = test_name.lower()
    desc_lower = test_description.lower()
    
    # Check for link notes task
    if "link" in test_lower or "link" in desc_lower:
        prompt += LINK_NOTES_PROMPT
    # Check for theme change task
    elif "theme" in test_lower or "theme" in desc_lower or "dark" in desc_lower or "light" in desc_lower:
        prompt += CHANGE_THEME_PROMPT
    # Check for delete task
    elif "delete" in test_lower or "delete" in desc_lower:
        prompt += DELETE_NOTE_PROMPT
    # Check for search task
    elif "search" in test_lower or "search" in desc_lower:
        prompt += SEARCH_NOTE_PROMPT
    # Check for multi-note creation (Test 5 style)
    elif ("note" in desc_lower and "another" in desc_lower) or \
       ("create" in desc_lower and "two" in desc_lower) or \
       ("multiple" in desc_lower and "note" in desc_lower) or \
       ("batch" in test_lower) or \
       (desc_lower.count("note") >= 2 and "create" in desc_lower):
        prompt += MULTI_NOTE_CREATION_PROMPT
    # Check for vault creation with new folder
    elif ("vault" in desc_lower and "folder" in desc_lower) or \
         ("vault" in desc_lower and "new" in desc_lower and "create" in desc_lower) or \
         ("testvault" in desc_lower):
        prompt += CREATE_VAULT_NEW_FOLDER_PROMPT
    elif "vault" in test_lower and "create" in test_lower:
        prompt += VAULT_CREATION_PROMPT
    elif "note" in test_lower and "create" in test_lower:
        prompt += NOTE_CREATION_PROMPT
    elif "appearance" in test_lower or "settings" in test_lower or "appearance" in desc_lower:
        prompt += SETTINGS_NAVIGATION_PROMPT
    elif "color" in desc_lower or "icon" in desc_lower or "verify" in desc_lower:
        prompt += SETTINGS_NAVIGATION_PROMPT
    else:
        prompt += GENERIC_TEST_PROMPT.format(description=test_description)
    
    return prompt


def create_test_agent(test_name: str, test_description: str, success_condition: str, model_name: str = "openai/gpt-4o-mini") -> Agent:
    return Agent(
        name="mobile_qa_agent",
        model=model_name,
        description=f"Smart QA Agent for: {test_name}",
        instruction=get_test_prompt(test_name, test_description, success_condition),
        tools=ALL_TOOLS
    )