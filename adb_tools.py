"""
ADB Tools Module - Enhanced with UI Element Detection
======================================================
Provides functions to interact with Android devices via ADB.
Includes UI hierarchy parsing to find actual element coordinates.
"""

import subprocess
import base64
import time
import re
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Tuple


def take_screenshot() -> str:
    """
    Take a screenshot and return as base64-encoded PNG.
    Returns base64 string on success, error message on failure.
    """
    try:
        result = subprocess.run(
            ["adb", "exec-out", "screencap", "-p"],
            capture_output=True,
            timeout=15
        )
        
        if result.returncode == 0 and len(result.stdout) > 0:
            return base64.b64encode(result.stdout).decode('utf-8')
        else:
            return f"Error: Screenshot failed - {result.stderr.decode()}"
    except subprocess.TimeoutExpired:
        return "Error: Screenshot timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def get_ui_hierarchy() -> str:
    """
    Dump the UI hierarchy XML from the device.
    Returns XML string or error message.
    """
    try:
        # Dump UI hierarchy to device
        subprocess.run(
            ["adb", "shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"],
            capture_output=True,
            timeout=10
        )
        
        # Pull the XML content
        result = subprocess.run(
            ["adb", "shell", "cat", "/sdcard/ui_dump.xml"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: UI dump timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def parse_ui_elements(xml_content: str) -> List[Dict]:
    """
    Parse UI hierarchy XML and extract clickable elements with their bounds.
    Returns list of elements with text, bounds, and center coordinates.
    """
    elements = []
    
    try:
        # Clean up XML if needed
        xml_content = xml_content.strip()
        if not xml_content.startswith('<?xml'):
            # Find the start of XML
            start = xml_content.find('<?xml')
            if start != -1:
                xml_content = xml_content[start:]
        
        root = ET.fromstring(xml_content)
        
        def parse_bounds(bounds_str: str) -> Tuple[int, int, int, int]:
            """Parse bounds string like '[0,100][1080,200]' to (x1, y1, x2, y2)"""
            match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
            if match:
                return tuple(map(int, match.groups()))
            return (0, 0, 0, 0)
        
        def traverse(node, depth=0):
            # Get node attributes
            text = node.get('text', '')
            content_desc = node.get('content-desc', '')
            resource_id = node.get('resource-id', '')
            class_name = node.get('class', '')
            clickable = node.get('clickable', 'false') == 'true'
            focusable = node.get('focusable', 'false') == 'true'
            focused = node.get('focused', 'false') == 'true'
            bounds_str = node.get('bounds', '[0,0][0,0]')
            
            bounds = parse_bounds(bounds_str)
            x1, y1, x2, y2 = bounds
            
            # Calculate center
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # Include elements with text, clickable, or focusable
            if (text or content_desc or clickable or focusable) and (x2 - x1) > 10 and (y2 - y1) > 10:
                elements.append({
                    'text': text,
                    'content_desc': content_desc,
                    'resource_id': resource_id,
                    'class': class_name,
                    'clickable': clickable,
                    'focusable': focusable,
                    'focused': focused,
                    'bounds': bounds,
                    'center_x': center_x,
                    'center_y': center_y,
                    'width': x2 - x1,
                    'height': y2 - y1
                })
            
            # Recurse into children
            for child in node:
                traverse(child, depth + 1)
        
        traverse(root)
        
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
    except Exception as e:
        print(f"Error parsing UI: {e}")
    
    return elements


def find_element_by_text(text: str, partial: bool = True, prefer_clickable: bool = True) -> Optional[Dict]:
    """
    Find a UI element by its text content.
    If prefer_clickable is True, prioritizes clickable elements (buttons) over labels.
    Returns element dict with coordinates or None.
    """
    xml = get_ui_hierarchy()
    if xml.startswith("Error"):
        print(f"Could not get UI hierarchy: {xml}")
        return None
    
    elements = parse_ui_elements(xml)
    
    text_lower = text.lower()
    matches = []
    
    for elem in elements:
        elem_text = (elem.get('text', '') + ' ' + elem.get('content_desc', '')).lower()
        if partial:
            if text_lower in elem_text:
                matches.append(elem)
        else:
            if text_lower == elem_text.strip():
                matches.append(elem)
    
    if not matches:
        return None
    
    if len(matches) == 1:
        return matches[0]
    
    # Multiple matches - prioritize clickable buttons
    if prefer_clickable:
        # First, look for actual Button class
        for elem in matches:
            class_name = elem.get('class', '').lower()
            if 'button' in class_name:
                return elem
        
        # Next, look for clickable elements
        for elem in matches:
            if elem.get('clickable'):
                return elem
        
        # Next, prefer elements in the lower half of screen (buttons usually at bottom)
        bottom_elements = [e for e in matches if e.get('center_y', 0) > 1200]
        if bottom_elements:
            return bottom_elements[0]
    
    # Return first match as fallback
    return matches[0]


def find_input_field(label_text: str = None) -> Optional[Dict]:
    """
    Find an input field (EditText) on screen.
    If label_text is provided, tries to find the input field near that label.
    Returns the input field element with coordinates.
    """
    xml = get_ui_hierarchy()
    if xml.startswith("Error"):
        return None
    
    elements = parse_ui_elements(xml)
    
    # Find all EditText elements (input fields)
    input_fields = []
    for elem in elements:
        class_name = elem.get('class', '')
        resource_id = elem.get('resource_id', '')
        
        # Check if it's an EditText
        if 'EditText' in class_name or 'edittext' in class_name.lower():
            input_fields.append(elem)
            continue
            
        # Check if it has an edit-related resource ID
        if 'edit' in resource_id.lower() or 'input' in resource_id.lower():
            input_fields.append(elem)
            continue
    
    # Also look for elements that look like input fields by their properties
    for elem in elements:
        if elem in input_fields:
            continue
            
        # Input fields often have placeholder text
        text = elem.get('text', '')
        if text in ['My vault', 'Write here', 'Enter text', 'Type here', '']:
            # Empty text with focusable is likely an input field
            if elem.get('focusable') and elem.get('clickable'):
                # Make sure it's not too small (likely a button) and has reasonable dimensions
                if elem.get('height', 0) > 40 and elem.get('width', 0) > 200:
                    input_fields.append(elem)
    
    if not input_fields:
        # Fallback: look for focusable elements that aren't buttons
        for elem in elements:
            if elem.get('focusable') and 'Button' not in elem.get('class', ''):
                # Skip if it's clearly a label (has "Vault name" etc.)
                text = elem.get('text', '')
                if text and text not in ['Vault name', 'Vault location']:
                    input_fields.append(elem)
    
    if not input_fields:
        # Fallback: look for elements below labels
        if label_text:
            label = find_element_by_text(label_text)
            if label:
                label_y = label['center_y']
                # Find clickable elements just below the label
                for elem in elements:
                    if elem['center_y'] > label_y and elem['center_y'] < label_y + 200:
                        if elem.get('clickable') or elem.get('text'):
                            input_fields.append(elem)
                            break
    
    if input_fields:
        # Return the first (topmost) input field, or the one nearest to label
        if label_text:
            label = find_element_by_text(label_text)
            if label:
                label_y = label['center_y']
                # Find input field closest to and below the label
                best = None
                best_dist = float('inf')
                for field in input_fields:
                    if field['center_y'] > label_y:  # Must be below label
                        dist = field['center_y'] - label_y
                        if dist < best_dist:
                            best_dist = dist
                            best = field
                if best:
                    return best
        return input_fields[0]
    
    return None


def get_input_field_coordinates(label_text: str = None) -> Optional[Tuple[int, int]]:
    """
    Find an input field and return its center coordinates.
    More reliable than trying to tap by label text!
    """
    field = find_input_field(label_text)
    if field:
        return (field['center_x'], field['center_y'])
    return None


def find_clickable_elements() -> List[Dict]:
    """
    Get all clickable elements on screen with their positions.
    Useful for debugging coordinate issues.
    """
    xml = get_ui_hierarchy()
    if xml.startswith("Error"):
        return []
    
    elements = parse_ui_elements(xml)
    return [e for e in elements if e.get('clickable') or e.get('text')]


def get_element_coordinates(text: str) -> Optional[Tuple[int, int]]:
    """
    Find an element by text and return its center coordinates.
    Prefers clickable buttons over text labels.
    """
    element = find_element_by_text(text, prefer_clickable=True)
    if element:
        return (element['center_x'], element['center_y'])
    return None


def tap(x: int, y: int) -> str:
    """Tap at the specified coordinates."""
    try:
        result = subprocess.run(
            ["adb", "shell", "input", "tap", str(x), str(y)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return f"Tapped at ({x}, {y})"
        else:
            return f"Failed to tap: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Tap timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def tap_element(text: str) -> str:
    """
    Find a BUTTON/clickable element by text and tap on it.
    Prioritizes clickable elements over text labels.
    """
    element = find_element_by_text(text, prefer_clickable=True)
    if element:
        x, y = element['center_x'], element['center_y']
        is_clickable = element.get('clickable', False)
        elem_class = element.get('class', 'unknown')
        
        # Log what we found for debugging
        print(f"   📍 Found '{text}': class={elem_class}, clickable={is_clickable}, pos=({x}, {y})")
        
        # Warning if we might be tapping a label instead of button
        if not is_clickable and y < 500:
            print(f"   ⚠️  Warning: This might be a title/label, not a button!")
        
        result = tap(x, y)
        return f"Found '{text}' at ({x}, {y}). {result}"
    else:
        return f"Error: Could not find element with text '{text}'"


def tap_input_by_label(label_text: str) -> str:
    """
    Find an input field by its label and tap on it.
    Handles the stylus popup automatically.
    """
    coords = get_input_field_coordinates(label_text)
    if coords:
        x, y = coords
        # Use tap_input_field which handles stylus popup
        result = tap_input_field(x, y)
        return f"Found input field for '{label_text}' at ({x}, {y}). {result}"
    else:
        # Fallback: try to find by placeholder text
        field = find_input_field()
        if field:
            x, y = field['center_x'], field['center_y']
            result = tap_input_field(x, y)
            return f"Found input field at ({x}, {y}). {result}"
        return f"Error: Could not find input field for '{label_text}'"


def dismiss_stylus_popup() -> str:
    """Dismiss the 'Try out your stylus' popup by pressing back."""
    try:
        time.sleep(0.3)
        subprocess.run(
            ["adb", "shell", "input", "keyevent", "4"],
            capture_output=True,
            timeout=5
        )
        time.sleep(0.3)
        return "Dismissed popup"
    except Exception as e:
        return f"Error dismissing popup: {str(e)}"


def tap_input_field(x: int, y: int) -> str:
    """
    Tap on an input field, handling the stylus popup that appears.
    """
    try:
        tap(x, y)
        time.sleep(0.5)
        dismiss_stylus_popup()
        tap(x, y)
        time.sleep(0.3)
        return f"Focused input field at ({x}, {y})"
    except Exception as e:
        return f"Error: {str(e)}"


def swipe(start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 300) -> str:
    """Perform a swipe gesture."""
    try:
        result = subprocess.run(
            ["adb", "shell", "input", "swipe", 
             str(start_x), str(start_y), str(end_x), str(end_y), str(duration_ms)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})"
        else:
            return f"Failed to swipe: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Swipe timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def type_text(text: str) -> str:
    """Type text into the currently focused input field."""
    try:
        # Escape special characters for ADB
        escaped_text = text.replace(" ", "%s")
        escaped_text = escaped_text.replace("'", "\\'")
        escaped_text = escaped_text.replace('"', '\\"')
        escaped_text = escaped_text.replace("&", "\\&")
        escaped_text = escaped_text.replace("|", "\\|")
        escaped_text = escaped_text.replace(";", "\\;")
        escaped_text = escaped_text.replace("(", "\\(")
        escaped_text = escaped_text.replace(")", "\\)")
        
        result = subprocess.run(
            ["adb", "shell", "input", "text", escaped_text],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            return f"Typed: {text}"
        else:
            return f"Failed to type: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Typing timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def select_all() -> str:
    """Select all text in the current field (Ctrl+A)."""
    try:
        result = subprocess.run(
            ["adb", "shell", "input", "keyevent", "KEYCODE_CTRL_LEFT", "KEYCODE_A"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Alternative method using keyevent combination
        subprocess.run(
            ["adb", "shell", "input", "keycombination", "113", "29"],  # CTRL + A
            capture_output=True,
            timeout=5
        )
        return "Selected all text"
    except Exception as e:
        # Fallback: use move to start + shift+end to select all
        try:
            # Move to end
            subprocess.run(["adb", "shell", "input", "keyevent", "123"], capture_output=True, timeout=5)  # MOVE_END
            # Select all by shift+home
            subprocess.run(["adb", "shell", "input", "keyevent", "--longpress", "122"], capture_output=True, timeout=5)
            return "Selected all text (fallback)"
        except:
            return f"Error selecting all: {str(e)}"


def clear_field() -> str:
    """Clear all text in the currently focused input field."""
    try:
        # Method 1: Triple-tap to select all, then delete
        # First, try selecting all with long press (some apps support this)
        
        # Method 2: Move to end, then delete backwards multiple times
        # Move to end of field
        subprocess.run(
            ["adb", "shell", "input", "keyevent", "123"],  # KEYCODE_MOVE_END
            capture_output=True,
            timeout=5
        )
        time.sleep(0.1)
        
        # Delete backwards multiple times (handle up to 50 characters)
        for _ in range(50):
            subprocess.run(
                ["adb", "shell", "input", "keyevent", "67"],  # KEYCODE_DEL (backspace)
                capture_output=True,
                timeout=2
            )
        
        return "Cleared field"
    except Exception as e:
        return f"Error clearing field: {str(e)}"


def clear_and_type(text: str) -> str:
    """Clear the current field and type new text."""
    try:
        # First clear the field
        clear_result = clear_field()
        time.sleep(0.2)
        
        # Then type the new text
        type_result = type_text(text)
        
        return f"{clear_result}. {type_result}"
    except Exception as e:
        return f"Error: {str(e)}"


def press_back() -> str:
    """Press the Android back button."""
    try:
        result = subprocess.run(
            ["adb", "shell", "input", "keyevent", "4"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return "Pressed back button"
        else:
            return f"Failed to press back: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Press back timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def press_enter() -> str:
    """Press the enter/submit key."""
    try:
        result = subprocess.run(
            ["adb", "shell", "input", "keyevent", "66"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return "Pressed enter"
        else:
            return f"Failed to press enter: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Press enter timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def press_home() -> str:
    """Press the Android home button."""
    try:
        result = subprocess.run(
            ["adb", "shell", "input", "keyevent", "3"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return "Pressed home button"
        else:
            return f"Failed to press home: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Press home timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def launch_app(package_name: str) -> str:
    """Launch an app by package name."""
    try:
        result = subprocess.run(
            ["adb", "shell", "monkey", "-p", package_name, 
             "-c", "android.intent.category.LAUNCHER", "1"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return f"Launched {package_name}"
        else:
            return f"Failed to launch: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Launch timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def wait(seconds: float) -> str:
    """Wait for specified seconds."""
    time.sleep(seconds)
    return f"Waited {seconds}s"


def get_screen_size() -> Tuple[int, int]:
    """Get the screen resolution of the connected device."""
    try:
        result = subprocess.run(
            ["adb", "shell", "wm", "size"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "Physical size:" in output:
                size_str = output.split("Physical size:")[-1].strip()
                width, height = size_str.split("x")
                return (int(width), int(height))
        return (1080, 2400)
    except Exception:
        return (1080, 2400)


def clear_app_data(package_name: str) -> str:
    """Clear app data (reset to fresh state)."""
    try:
        result = subprocess.run(
            ["adb", "shell", "pm", "clear", package_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return f"Cleared data for {package_name}"
        else:
            return f"Failed to clear data: {result.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


def force_stop_app(package_name: str) -> str:
    """Force stop an app."""
    try:
        result = subprocess.run(
            ["adb", "shell", "am", "force-stop", package_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return f"Force stopped {package_name}"
        else:
            return f"Failed to force stop: {result.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


def get_screen_elements_description() -> str:
    """
    Get a text description of all UI elements on screen.
    This can be added to the prompt to help the AI understand what's available.
    """
    elements = find_clickable_elements()
    
    if not elements:
        return "Could not detect UI elements."
    
    description = "DETECTED UI ELEMENTS:\n"
    for i, elem in enumerate(elements, 1):
        text = elem.get('text') or elem.get('content_desc') or '[no text]'
        x, y = elem['center_x'], elem['center_y']
        clickable = "clickable" if elem.get('clickable') else "not clickable"
        description += f"  {i}. '{text}' at ({x}, {y}) - {clickable}\n"
    
    return description


# Test function
if __name__ == "__main__":
    print("Testing UI detection...")
    print("\nScreen size:", get_screen_size())
    print("\nClickable elements on screen:")
    elements = find_clickable_elements()
    for elem in elements:
        text = elem.get('text') or elem.get('content_desc') or '[no text]'
        print(f"  '{text}' at ({elem['center_x']}, {elem['center_y']})")
    
    # Test finding specific element
    print("\nLooking for 'Continue without sync':")
    coords = get_element_coordinates("Continue without sync")
    if coords:
        print(f"  Found at: {coords}")
    else:
        print("  Not found")