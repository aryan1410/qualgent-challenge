"""
ADB Tools for Mobile QA Agent
=============================
Functions to interact with Android devices via ADB and UI Automator.
"""

import subprocess
import base64
import time
import re
import os
from typing import Dict, List, Optional, Tuple


def run_adb_command(args: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run an ADB command and return the result."""
    cmd = ["adb"] + args
    return subprocess.run(cmd, capture_output=capture_output, text=True, encoding='utf-8', errors='replace')


def take_screenshot() -> str:
    """
    Take a screenshot and return as base64 string.
    
    Returns:
        str: Base64 encoded PNG image, or error message
    """
    try:
        result = subprocess.run(
            ["adb", "exec-out", "screencap", "-p"],
            capture_output=True
        )
        if result.returncode != 0:
            return f"Error: Screenshot failed - {result.stderr}"
        
        b64_image = base64.b64encode(result.stdout).decode('utf-8')
        return b64_image
    except Exception as e:
        return f"Error: {str(e)}"


def take_screenshot_compressed(max_width: int = 270, quality: int = 40) -> str:
    """
    Take a screenshot, resize it, and compress to reduce token usage.
    
    Args:
        max_width: Maximum width to resize to (height scales proportionally)
        quality: JPEG quality (1-100, lower = smaller file)
    
    Returns:
        str: Base64 encoded JPEG image, or error message
    """
    try:
        from PIL import Image
        import io
        
        # Take screenshot
        result = subprocess.run(
            ["adb", "exec-out", "screencap", "-p"],
            capture_output=True
        )
        if result.returncode != 0:
            return f"Error: Screenshot failed - {result.stderr}"
        
        # Open image with PIL
        img = Image.open(io.BytesIO(result.stdout))
        
        # Resize - make it much smaller
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB (JPEG doesn't support alpha)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Compress as JPEG with low quality
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        
        b64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        print(f"[screenshot] Compressed to {max_width}x{new_height}, size={len(b64_image)} chars")
        return b64_image
    except ImportError:
        print("[screenshot] PIL not available, skipping screenshot")
        return None
    except Exception as e:
        print(f"[screenshot] Error: {str(e)}")
        return None


def get_screen_size() -> Tuple[int, int]:
    """
    Get the screen dimensions.
    
    Returns:
        Tuple[int, int]: (width, height)
    """
    try:
        result = run_adb_command(["shell", "wm", "size"])
        match = re.search(r'(\d+)x(\d+)', result.stdout)
        if match:
            return int(match.group(1)), int(match.group(2))
    except:
        pass
    return 1080, 2400  # Default


def tap(x: int, y: int) -> str:
    """
    Tap at specific coordinates.
    
    Args:
        x: X coordinate
        y: Y coordinate
    
    Returns:
        str: Result message
    """
    try:
        run_adb_command(["shell", "input", "tap", str(x), str(y)])
        return f"Tapped at ({x}, {y})"
    except Exception as e:
        return f"Error: {str(e)}"


def type_text(text: str) -> str:
    """
    Type text into the focused field.
    
    Args:
        text: Text to type
    
    Returns:
        str: Result message
    """
    try:
        # Escape spaces for ADB
        escaped_text = text.replace(" ", "%s").replace("'", "\\'")
        run_adb_command(["shell", "input", "text", escaped_text])
        return f"Typed: {text}"
    except Exception as e:
        return f"Error: {str(e)}"


def press_enter() -> str:
    """Press the Enter/Done key."""
    try:
        run_adb_command(["shell", "input", "keyevent", "66"])
        return "Pressed enter"
    except Exception as e:
        return f"Error: {str(e)}"


def press_back() -> str:
    """Press the Back button."""
    try:
        run_adb_command(["shell", "input", "keyevent", "4"])
        return "Pressed back"
    except Exception as e:
        return f"Error: {str(e)}"


def swipe(start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 300) -> str:
    """
    Perform a swipe gesture.
    
    Args:
        start_x, start_y: Starting coordinates
        end_x, end_y: Ending coordinates
        duration_ms: Duration in milliseconds
    
    Returns:
        str: Result message
    """
    try:
        run_adb_command([
            "shell", "input", "swipe",
            str(start_x), str(start_y),
            str(end_x), str(end_y),
            str(duration_ms)
        ])
        return f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})"
    except Exception as e:
        return f"Error: {str(e)}"


def clear_field() -> str:
    """Clear the current input field by selecting all and deleting."""
    try:
        # Move to end
        run_adb_command(["shell", "input", "keyevent", "123"])  # MOVE_END
        time.sleep(0.1)
        
        # Backspace multiple times
        for _ in range(50):
            run_adb_command(["shell", "input", "keyevent", "67"])  # DEL
        
        return "Cleared field"
    except Exception as e:
        return f"Error: {str(e)}"


def clear_and_type(text: str) -> str:
    """Clear the field and type new text."""
    clear_result = clear_field()
    if "Error" in clear_result:
        return clear_result
    
    time.sleep(0.2)
    return type_text(text)


def get_ui_hierarchy() -> str:
    """
    Dump the UI hierarchy XML from the device.
    
    Returns:
        str: XML string of UI hierarchy
    """
    try:
        # Dump UI to file on device
        run_adb_command(["shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"])
        time.sleep(0.3)
        
        # Read the file with explicit UTF-8 handling
        result = subprocess.run(
            ["adb", "shell", "cat", "/sdcard/ui_dump.xml"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.stdout:
            return result.stdout
        else:
            return "Error: Empty UI hierarchy"
    except Exception as e:
        return f"Error: {str(e)}"


def parse_ui_elements(xml: str) -> List[Dict]:
    """
    Parse UI hierarchy XML into list of elements.
    
    Args:
        xml: UI hierarchy XML string
    
    Returns:
        List[Dict]: List of UI elements with properties
    """
    elements = []
    
    # Find all node elements
    node_pattern = r'<node[^>]+>'
    for match in re.finditer(node_pattern, xml):
        node = match.group()
        
        # Extract text
        text_match = re.search(r'text="([^"]*)"', node)
        text = text_match.group(1) if text_match else ""
        
        # Extract content-desc
        desc_match = re.search(r'content-desc="([^"]*)"', node)
        content_desc = desc_match.group(1) if desc_match else ""
        
        # Extract class
        class_match = re.search(r'class="([^"]*)"', node)
        class_name = class_match.group(1) if class_match else ""
        
        # Extract bounds
        bounds_match = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
        if bounds_match:
            x1, y1, x2, y2 = map(int, bounds_match.groups())
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            width = x2 - x1
            height = y2 - y1
        else:
            center_x, center_y, width, height = 0, 0, 0, 0
        
        # Extract properties
        clickable = 'clickable="true"' in node
        focusable = 'focusable="true"' in node
        
        # Extract resource-id
        resource_match = re.search(r'resource-id="([^"]*)"', node)
        resource_id = resource_match.group(1) if resource_match else ""
        
        elements.append({
            'text': text,
            'content_desc': content_desc,
            'class': class_name,
            'clickable': clickable,
            'focusable': focusable,
            'center_x': center_x,
            'center_y': center_y,
            'width': width,
            'height': height,
            'bounds': (x1, y1, x2, y2) if bounds_match else None,
            'resource_id': resource_id
        })
    
    return elements


def find_clickable_elements() -> List[Dict]:
    """
    Find all clickable/interactive elements on screen.
    
    Returns:
        List[Dict]: List of interactive elements
    """
    xml = get_ui_hierarchy()
    if xml.startswith("Error"):
        return []
    
    elements = parse_ui_elements(xml)
    
    # Filter to elements with text or that are clickable
    interactive = []
    for elem in elements:
        if elem.get('text') or elem.get('content_desc') or elem.get('clickable'):
            interactive.append(elem)
    
    return interactive


def find_element_by_text(text: str, prefer_clickable: bool = True) -> Optional[Dict]:
    """
    Find an element by its text, prioritizing clickable elements.
    
    Args:
        text: Text to search for
        prefer_clickable: If True, prioritize clickable matches
    
    Returns:
        Optional[Dict]: Element info or None
    """
    xml = get_ui_hierarchy()
    if xml.startswith("Error"):
        return None
    
    elements = parse_ui_elements(xml)
    text_lower = text.lower().strip()
    
    # Find all matches
    matches = []
    for elem in elements:
        elem_text = (elem.get('text') or '').lower().strip()
        elem_desc = (elem.get('content_desc') or '').lower().strip()
        
        if text_lower in elem_text or text_lower in elem_desc:
            matches.append(elem)
        elif elem_text and text_lower == elem_text:
            matches.append(elem)
    
    if not matches:
        return None
    
    if len(matches) == 1:
        return matches[0]
    
    # Multiple matches - prioritize
    if prefer_clickable:
        # Priority 1: Button class
        for elem in matches:
            if 'button' in elem.get('class', '').lower():
                return elem
        
        # Priority 2: Clickable
        for elem in matches:
            if elem.get('clickable'):
                return elem
        
        # Priority 3: Bottom of screen (buttons usually there)
        bottom_elements = [e for e in matches if e.get('center_y', 0) > 1200]
        if bottom_elements:
            return bottom_elements[0]
    
    return matches[0]


def tap_element(text: str) -> str:
    """
    Find an element by text and tap it.
    
    Args:
        text: Text of element to tap
    
    Returns:
        str: Result message
    """
    element = find_element_by_text(text, prefer_clickable=True)
    
    if not element:
        return f"Error: Element '{text}' not found on screen"
    
    x = element['center_x']
    y = element['center_y']
    
    # Log what we found
    class_name = element.get('class', 'unknown')
    clickable = element.get('clickable', False)
    
    tap(x, y)
    return f"Found '{text}' at ({x}, {y}) [class={class_name}, clickable={clickable}]. Tapped."


def tap_input_field(x: int, y: int) -> str:
    """
    Tap an input field, handling stylus popup.
    
    Args:
        x: X coordinate
        y: Y coordinate
    
    Returns:
        str: Result message
    """
    # First tap may trigger stylus popup
    tap(x, y)
    time.sleep(0.5)
    
    # Press back to dismiss any popup
    press_back()
    time.sleep(0.3)
    
    # Second tap to actually focus
    tap(x, y)
    
    return f"Focused input field at ({x}, {y})"


def find_input_field(label_text: str = None) -> Optional[Dict]:
    """
    Find an input field on screen.
    
    Args:
        label_text: Optional label to look for near the input
    
    Returns:
        Optional[Dict]: Input field element or None
    """
    xml = get_ui_hierarchy()
    if xml.startswith("Error"):
        return None
    
    elements = parse_ui_elements(xml)
    
    input_fields = []
    for elem in elements:
        class_name = elem.get('class', '')
        text = elem.get('text', '')
        
        # EditText is an input field
        if 'EditText' in class_name:
            input_fields.append(elem)
            continue
        
        # Check for input-like resource IDs
        resource_id = elem.get('resource_id', '')
        if 'edit' in resource_id.lower() or 'input' in resource_id.lower():
            input_fields.append(elem)
            continue
        
        # Placeholder text indicators
        if text in ['My vault', 'Write here', 'Enter text', 'Type here']:
            input_fields.append(elem)
            continue
        
        # Note titles
        if text.startswith('Untitled'):
            input_fields.append(elem)
    
    if input_fields:
        # If label provided, find closest
        if label_text:
            label_elem = find_element_by_text(label_text)
            if label_elem:
                label_y = label_elem['center_y']
                # Find input below label
                below_label = [f for f in input_fields if f['center_y'] > label_y]
                if below_label:
                    return min(below_label, key=lambda f: f['center_y'] - label_y)
        
        return input_fields[0]
    
    return None


def launch_app(package_name: str) -> str:
    """
    Launch an app by package name.
    
    Args:
        package_name: Android package name (e.g., "md.obsidian")
    
    Returns:
        str: Result message
    """
    try:
        run_adb_command([
            "shell", "monkey",
            "-p", package_name,
            "-c", "android.intent.category.LAUNCHER", "1"
        ])
        time.sleep(2)
        return f"Launched {package_name}"
    except Exception as e:
        return f"Error: {str(e)}"


def clear_app_data(package_name: str) -> str:
    """
    Clear app data (reset to fresh state).
    
    Args:
        package_name: Android package name
    
    Returns:
        str: Result message
    """
    try:
        run_adb_command(["shell", "pm", "clear", package_name])
        return f"Cleared data for {package_name}"
    except Exception as e:
        return f"Error: {str(e)}"


def check_device_connected() -> bool:
    """Check if an Android device is connected."""
    try:
        result = run_adb_command(["devices"])
        lines = result.stdout.strip().split('\n')
        # First line is header, subsequent lines are devices
        return len(lines) > 1 and 'device' in lines[1]
    except:
        return False


def get_current_package() -> str:
    """Get the currently focused app package name."""
    try:
        result = run_adb_command([
            "shell", "dumpsys", "window", "windows",
            "|", "grep", "-E", "mCurrentFocus"
        ])
        match = re.search(r'(\w+\.\w+[\w.]*)', result.stdout)
        if match:
            return match.group(1)
    except:
        pass
    return "unknown"