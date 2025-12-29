# 🔧 Tools Reference

## Overview

The Mobile QA Agent has 7 tools available for interacting with the Android device. Each tool is a function that the AI agent can call to perform actions or gather information.

---

## Tool Summary

| Tool | Purpose | Returns |
|------|---------|---------|
| `get_screen_elements` | See current screen state | Screenshot + UI elements |
| `tap_at_coordinates` | Tap at exact (x, y) position | Success/failure |
| `tap_element_by_text` | Find element by text and tap | Success/failure |
| `type_text_input` | Tap input field and type text | Success/failure |
| `press_enter_key` | Press Enter key | Success/failure |
| `press_back_button` | Press Back button | Success/failure |
| `swipe_screen` | Scroll up or down | Success/failure |

---

## Detailed Tool Documentation

### 1. get_screen_elements

**Purpose**: Capture the current screen state including a compressed screenshot and list of UI elements with their coordinates.

**Parameters**: None

**Returns**:
```python
{
    "screenshot_base64": str,     # Compressed JPEG image (base64)
    "elements": [                  # List of UI elements
        {
            "text": str,           # Element text or "[input field]"
            "x": int,              # Center X coordinate
            "y": int,              # Center Y coordinate
            "width": int,          # Element width
            "height": int,         # Element height
            "type": str,           # "button", "input", or "text"
            "clickable": bool      # Whether element is clickable
        },
        ...
    ],
    "screen_type": str,            # Detected screen type
    "element_count": int,          # Number of elements found
    "hint": str                    # Usage hint for agent
}
```

**Screen Types Detected**:
- `initial_vault_choice` - App launch screen
- `sync_setup` - Sync configuration screen
- `vault_configuration` - Vault naming screen
- `folder_picker` - File/folder selection
- `permission_dialog` - Permission request
- `inside_vault` - Inside a vault
- `note_editor` - Editing a note (untitled)
- `note_editor_with_title` - Editing a note (with title)
- `settings_screen` - Settings menu
- `appearance_settings` - Appearance settings
- `unknown` - Unrecognized screen

**Example Usage**:
```python
result = get_screen_elements()
# Agent sees screenshot and elements like:
# "Create a vault" at (540, 385) type=button
# "Use my existing vault" at (540, 450) type=button
```

**Notes**:
- Screenshot is compressed to ~270px width, JPEG at 40% quality
- Elements are sorted top-to-bottom by Y coordinate
- Maximum 20 elements returned to avoid token overflow
- Full-screen container elements are filtered out

---

### 2. tap_at_coordinates

**Purpose**: Tap at exact screen coordinates. Use when you know the precise location.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `x` | int | Yes | X coordinate (0-1080) |
| `y` | int | Yes | Y coordinate (0-2400) |

**Returns**:
```python
{
    "success": bool,
    "message": str  # "Tapped at (x, y)"
}
```

**Example Usage**:
```python
# Tap the + button at bottom bar
tap_at_coordinates(600, 2292)

# Tap expand sidebar button
tap_at_coordinates(100, 128)
```

**Common Coordinates**:
| Element | Coordinates |
|---------|-------------|
| Expand sidebar (top-left) | (100, 128) |
| Settings gear (in sidebar) | (280, 75) |
| Three dots menu (top-right) | (990, 128) |
| Search icon (bottom bar) | (148, 2292) |
| + icon (bottom bar) | (600, 2292) |
| New folder icon | (253, 128) |

---

### 3. tap_element_by_text

**Purpose**: Find an element by its text content and tap it. More robust than coordinates when element positions may vary.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | str | Yes | Text to search for (case-insensitive, partial match) |

**Returns**:
```python
{
    "success": bool,
    "message": str  # "Found 'text' at (x, y). Tapped." or error
}
```

**Example Usage**:
```python
# Tap buttons by their text
tap_element_by_text("Create a vault")
tap_element_by_text("Continue without sync")
tap_element_by_text("USE THIS FOLDER")
tap_element_by_text("Allow")
tap_element_by_text("Appearance")
tap_element_by_text("Delete file")
```

**Notes**:
- Search is case-insensitive
- Partial matches work ("Create" matches "Create a vault")
- Searches UI hierarchy, not screenshot
- Returns error if element not found

---

### 4. type_text_input

**Purpose**: Tap an input field, optionally clear it, then type text and dismiss keyboard.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `x` | int | Yes | - | X coordinate of input field |
| `y` | int | Yes | - | Y coordinate of input field |
| `text` | str | Yes | - | Text to type |
| `clear_first` | bool | No | True | Clear field before typing |

**Returns**:
```python
{
    "success": bool,
    "message": str  # "Typed 'text' at (x, y)"
}
```

**Example Usage**:
```python
# Enter vault name (clear existing text first)
type_text_input(540, 580, "InternVault", clear_first=True)

# Enter note title
type_text_input(540, 263, "Meeting Notes")

# Add to note body (don't clear)
type_text_input(540, 363, "Daily Standup", clear_first=False)

# Type link syntax
type_text_input(540, 329, "[[", clear_first=False)
```

**Process**:
1. Tap at (x, y) to focus the input field
2. If `clear_first=True`: Select all (Ctrl+A) and delete
3. Type the text character by character
4. Press Back to dismiss keyboard

**Notes**:
- Use `clear_first=False` when appending to existing content
- Keyboard is automatically dismissed after typing
- Special characters are handled by ADB input

---

### 5. press_enter_key

**Purpose**: Press the Enter key. Useful for confirming input or submitting forms.

**Parameters**: None

**Returns**:
```python
{
    "success": bool,
    "message": str  # "Pressed Enter"
}
```

**Example Usage**:
```python
# Confirm search query
press_enter_key()

# Submit form
press_enter_key()
```

**ADB Command**: `adb shell input keyevent 66`

---

### 6. press_back_button

**Purpose**: Press the Android Back button. Navigates back, dismisses dialogs, or closes keyboard.

**Parameters**: None

**Returns**:
```python
{
    "success": bool,
    "message": str  # "Pressed Back"
}
```

**Example Usage**:
```python
# Go back to previous screen
press_back_button()

# Dismiss popup/dialog
press_back_button()

# Close keyboard (though type_text_input does this automatically)
press_back_button()
```

**ADB Command**: `adb shell input keyevent 4`

**⚠️ Warning**: In some test scenarios (like multi-note creation), using Back button can navigate away from the current task. The prompts may specifically warn against using this tool.

---

### 7. swipe_screen

**Purpose**: Swipe/scroll the screen to reveal more content.

**Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `direction` | str | No | "up" | Direction to swipe: "up" or "down" |

**Returns**:
```python
{
    "success": bool,
    "message": str  # "Swiped up" or "Swiped down"
}
```

**Example Usage**:
```python
# Scroll down to see more content (swipe up)
swipe_screen("up")

# Scroll up to see previous content (swipe down)
swipe_screen("down")
```

**Swipe Mechanics**:
- `"up"` = Swipe from bottom to top = Scroll DOWN (see more below)
- `"down"` = Swipe from top to bottom = Scroll UP (see more above)

**ADB Command**: 
```bash
# Swipe up (scroll down)
adb shell input swipe 540 1500 540 500 300

# Swipe down (scroll up)
adb shell input swipe 540 500 540 1500 300
```

---

## Tool Call Flow

```
Agent Decision
      │
      ▼
┌─────────────────┐
│  Tool Function  │  (e.g., tap_at_coordinates)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   adb_tools.py  │  (low-level ADB wrapper)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ADB Command    │  (e.g., adb shell input tap 540 385)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Android Device  │  (executes action)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Return Result  │  (success/failure + message)
└─────────────────┘
```

---

## Best Practices

### When to Use Each Tool

| Scenario | Recommended Tool |
|----------|-----------------|
| Need to see what's on screen | `get_screen_elements` |
| Know exact button position | `tap_at_coordinates` |
| Button text is visible/known | `tap_element_by_text` |
| Need to enter text in a field | `type_text_input` |
| Need to scroll a list/menu | `swipe_screen` |
| Need to go back | `press_back_button` (use carefully) |

### Tool Call Patterns

**Standard Action Pattern**:
```
1. get_screen_elements()     # See current state
2. [action tool]             # Do something
3. get_screen_elements()     # Verify result
```

**Text Entry Pattern**:
```
1. get_screen_elements()     # Find input field
2. type_text_input(x, y, text)  # Enter text
3. get_screen_elements()     # Verify text entered
```

**Navigation Pattern**:
```
1. get_screen_elements()     # See current screen
2. tap_element_by_text("Button")  # Navigate
3. get_screen_elements()     # Confirm new screen
```

### Common Mistakes to Avoid

1. **Tapping without looking first**
   - Always call `get_screen_elements()` before tapping
   - Screen state may have changed

2. **Using coordinates that shift**
   - Element positions can vary based on content
   - Use `tap_element_by_text` when text is reliable

3. **Forgetting to verify actions**
   - Always check screen after important actions
   - Especially after navigation or form submission

4. **Over-using press_back_button**
   - Can accidentally exit the current flow
   - Often better to tap specific navigation elements