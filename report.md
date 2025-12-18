# QualGent Research Intern Challenge - Part 2
## Framework Decision Report & Implementation Details

**Author**: Aryan Shah
**Date**: December 18 2025
**Project**: Multi-Agent Mobile QA System for Obsidian App

---

## Executive Summary

This report documents the design, implementation, and evolution of a multi-agent mobile QA testing system built for the QualGent Research Intern Challenge. The system uses AI vision models to analyze Android app screenshots and execute automated test cases through ADB (Android Debug Bridge).

The final implementation successfully:
- Creates vaults in Obsidian with custom names
- Creates notes with specific titles and content
- Handles Android UI quirks (stylus popups, permissions)
- Detects test success/failure automatically
- Provides detailed bug reports when tests fail

---

## 1. Framework Evaluation

### Frameworks Considered

| Framework | Pros | Cons |
|-----------|------|------|
| **Simular Agent S3** | State-of-the-art (71.6% on AndroidWorld), purpose-built for mobile | Complex setup, heavy dependencies |
| **Google ADK** | Native multi-agent support, clean architecture | Not mobile-specific, general purpose |
| **Custom Solution** | Full control, educational value, free APIs | More manual implementation |

### Decision: Custom Multi-Agent Solution

I chose to build a custom solution for the following reasons:

1. **Learning Objective**: Building from scratch provides deeper understanding of multi-agent coordination, vision model integration, and mobile automation.

2. **Cost Efficiency**: Uses Groq's free tier API with Llama 4 Scout vision model - no paid services required.

3. **Flexibility**: Easy to debug, modify, and extend without framework constraints.

4. **Simplicity**: Clear separation of concerns with a straightforward Planner → Executor → Supervisor flow.

---

## 2. System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  MobileQAOrchestrator                        │
│              (Coordinates all agents & tests)                │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ PlannerAgent  │ │ ExecutorAgent │ │SupervisorAgent│
├───────────────┤ ├───────────────┤ ├───────────────┤
│ • Groq Llama 4│ │ • ADB Commands│ │ • Groq Llama 4│
│ • Vision      │ │ • UI Detection│ │ • Evaluation  │
│ • Decides     │ │ • Execute     │ │ • Bug Reports │
│   actions     │ │   taps/types  │ │ • Pass/Fail   │
└───────────────┘ └───────────────┘ └───────────────┘
```

### Agent Responsibilities

#### PlannerAgent
- **Input**: Screenshot (base64) + Test case description + UI element detection
- **Processing**: Analyzes current screen state, determines next action
- **Output**: Action JSON (tap_element, type_text, etc.)
- **Special Features**:
  - Loop detection (prevents infinite repetition)
  - Success detection (knows when test objective is achieved)
  - State machine enforcement (ensures proper action sequences)

#### ExecutorAgent
- **Input**: Action type + parameters
- **Processing**: Translates actions to ADB commands, validates coordinates
- **Output**: Execution result with before/after screenshots
- **Special Features**:
  - Auto-correction of wrong coordinates
  - Stylus popup handling
  - Input field detection

#### SupervisorAgent
- **Input**: Test case + action history + final screenshot
- **Processing**: Evaluates if test objective was achieved
- **Output**: PASS/FAIL verdict with reasoning and bug reports
- **Result Types**:
  - `test_passed`: Objective achieved
  - `test_assertion_failed`: App bug detected
  - `element_not_found`: Required UI element missing
  - `execution_error`: Test infrastructure issue

---

## 3. Key Technical Challenges & Solutions

### Challenge 1: API Rate Limits

**Problem**: Google Gemini free tier limited to ~8 vision requests before rate limiting.

**Solution**: Migrated to Groq API with Llama 4 Scout vision model.
- Free tier with generous limits (~100+ requests/day)
- Very fast inference
- OpenAI-compatible API for easy integration

```python
from groq import Groq
client = Groq(api_key=api_key)
model = "meta-llama/llama-4-scout-17b-16e-instruct"
```

### Challenge 2: Incorrect Tap Coordinates

**Problem**: Vision model outputting wrong Y coordinates. Buttons at bottom of screen (y≈2000) were being tapped at y≈450.

**Solution**: Implemented UI Automator integration for exact element detection.

```python
def get_ui_hierarchy() -> str:
    """Dump UI hierarchy XML from device."""
    subprocess.run(["adb", "shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"])
    result = subprocess.run(["adb", "shell", "cat", "/sdcard/ui_dump.xml"])
    return result.stdout
```

This provides exact coordinates for every UI element, eliminating coordinate guessing.

### Challenge 3: Duplicate Element Names

**Problem**: "Allow file access" appeared twice - as a title (y=357) and as a button (y=2000). System was tapping the title.

**Solution**: Prioritize clickable elements over text labels.

```python
def find_element_by_text(text: str, prefer_clickable: bool = True):
    matches = [elem for elem in elements if text in elem['text']]
    
    if prefer_clickable:
        # Prioritize actual Button class
        for elem in matches:
            if 'button' in elem['class'].lower():
                return elem
        # Then clickable elements
        for elem in matches:
            if elem.get('clickable'):
                return elem
        # Then bottom-of-screen elements
        for elem in matches:
            if elem['center_y'] > 1200:
                return elem
    
    return matches[0]
```

### Challenge 4: Android Stylus Popup

**Problem**: "Try out your stylus" popup appeared every time an input field was tapped, blocking text input.

**Solution**: Auto-dismiss popup with back button press.

```python
def tap_input_field(x: int, y: int) -> str:
    tap(x, y)           # Trigger field
    time.sleep(0.5)
    press_back()        # Dismiss stylus popup
    tap(x, y)           # Re-focus field
    return "Focused input field"
```

### Challenge 5: Skipped Type Actions

**Problem**: Agent would tap input field, then immediately tap submit button without typing text.

**Solution**: State machine enforcement that forces required action sequences.

```python
def _get_required_next_action(self, test_case: str) -> Optional[dict]:
    last_action = self.history[-1]
    
    # If we just tapped input, MUST type next
    if last_action['action_type'] in ['tap_input_by_label', 'tap_input']:
        return {
            "action_type": "type_text",
            "action_params": {"text": required_text}
        }
    
    # If we just typed, MUST press enter
    if last_action['action_type'] == 'type_text':
        return {
            "action_type": "press_enter",
            "action_params": {}
        }
```

### Challenge 6: Existing Text in Fields

**Problem**: Note title field had "Untitled 1" by default. Typing "Meeting Notes" resulted in "Untitled 1Meeting Notes".

**Solution**: Clear field before typing when existing text is present.

```python
def clear_field() -> str:
    """Clear text by moving to end and backspacing."""
    subprocess.run(["adb", "shell", "input", "keyevent", "123"])  # MOVE_END
    for _ in range(50):
        subprocess.run(["adb", "shell", "input", "keyevent", "67"])  # BACKSPACE
    return "Cleared field"

def clear_and_type(text: str) -> str:
    clear_field()
    type_text(text)
    return f"Cleared and typed: {text}"
```

### Challenge 7: Not Knowing When to Stop

**Problem**: Agent continued taking actions after test objective was achieved (e.g., kept clicking around after vault was created).

**Solution**: Automatic success detection based on screen state.

```python
def _check_test_success(self, test_case: str) -> Optional[dict]:
    elements = find_clickable_elements()
    all_text = ' '.join([e.get('text', '').lower() for e in elements])
    
    # Test 1: Create vault - success if we see note creation options
    if 'internvault' in test_case.lower():
        if 'create new note' in all_text:
            return {"action_type": "done", "result": "PASS"}
    
    # Test 2: Create note - success if we see title and content
    if 'meeting notes' in test_case.lower():
        if 'meeting notes' in all_text and 'daily standup' in all_text:
            return {"action_type": "done", "result": "PASS"}
```

---

## 4. Available Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `tap_element` | `{"text": "Button Text"}` | Find button by text and tap it |
| `tap_input_by_label` | `{"label": "Field Label"}` | Find input field and focus it |
| `tap` | `{"x": int, "y": int}` | Tap at exact coordinates |
| `tap_input` | `{"x": int, "y": int}` | Tap input field (handles stylus popup) |
| `type_text` | `{"text": "content"}` | Type into focused field |
| `clear_and_type` | `{"text": "content"}` | Clear field, then type |
| `clear_field` | `{}` | Clear current field |
| `press_back` | `{}` | Press Android back button |
| `press_enter` | `{}` | Press enter/done key |
| `swipe` | `{"start_x", "start_y", "end_x", "end_y"}` | Swipe gesture |
| `wait` | `{"seconds": float}` | Wait for UI |
| `done` | `{"result": "PASS/FAIL", "reason": "..."}` | Complete test |
| `failed` | `{"reason": "..."}` | Abort test |

---

## 5. Test Cases

| # | Test Case | Expected | Purpose |
|---|-----------|----------|---------|
| 1 | Create vault named 'InternVault' and enter it | PASS | Verify vault creation flow |
| 2 | Create note titled 'Meeting Notes' with 'Daily Standup' | PASS | Verify note creation |
| 3 | Verify Appearance icon is Red | FAIL | Bug detection (icon is purple) |
| 4 | Find 'Print to PDF' button | FAIL | Missing feature detection |

Tests 3 and 4 are intentionally designed to fail to demonstrate the system's ability to detect and report bugs/missing features.

---

## 6. Technology Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| Vision Model | Groq Llama 4 Scout | Free, fast, multimodal |
| Automation | ADB + UI Automator | Standard Android tools |
| Language | Python 3.10+ | Simple, good libraries |
| API Client | groq-python | Official SDK |

---

## 7. Project Structure

```
qualgent-v3/
├── main.py           # Entry point, test runner, interactive menu
├── agents.py         # PlannerAgent, ExecutorAgent, SupervisorAgent
├── adb_tools.py      # ADB wrapper functions, UI detection
├── prompts.py        # System prompts for each agent
├── requirements.txt  # Python dependencies
├── report.md         # This document
├── README.md         # Setup instructions
├── .env.example      # API key template
└── .gitignore        # Git ignore rules
```

---

## 8. Usage

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
echo "GROQ_API_KEY=your-key-here" > .env

# 3. Start Android emulator with Obsidian installed
emulator -avd Pixel_6_API_34

# 4. Reset Obsidian to fresh state
adb shell pm clear md.obsidian
```

### Running Tests

```bash
# Interactive menu
python main.py

# Run all tests
python main.py --all

# Run specific test
python main.py --test 1

# Reset Obsidian between test runs
adb shell pm clear md.obsidian
```

---

## 9. Sample Output

```
============================================================
📋 TEST: Create a new Vault named 'InternVault', and enter the vault.
============================================================

--- Step 1/20 ---
🔍 Planner analyzing (with UI detection)...
💭 I see a 'Create a vault' button. Tapping to start vault creation.
🎯 tap_element → {'text': 'Create a vault'}
📍 Found 'Create a vault': class=Button, clickable=True, pos=(540, 1030)
📱 Executor: ✓ Tapped at (540, 1030)

--- Step 2/20 ---
🔍 Planner analyzing (with UI detection)...
💭 I see 'Continue without sync' button. Tapping to proceed.
🎯 tap_element → {'text': 'Continue without sync'}
📱 Executor: ✓ Tapped at (540, 1303)

--- Step 3/20 ---
🔍 Planner analyzing (with UI detection)...
💭 I need to enter vault name. Tapping input field.
🎯 tap_input_by_label → {'label': 'Vault name'}
📱 Executor: ✓ Focused input field at (540, 608)

--- Step 4/20 ---
🔄 Auto-forcing type_text: 'InternVault'
🎯 type_text → {'text': 'InternVault'}
📱 Executor: ✓ Typed: InternVault

--- Step 5/20 ---
🔄 Auto-forcing press_enter after type_text
🎯 press_enter → {}
📱 Executor: ✓ Pressed enter

--- Step 6/20 ---
🔍 Planner analyzing (with UI detection)...
🎯 tap_element → {'text': 'Create a vault'}
📱 Executor: ✓ Tapped at (540, 1807)

--- Step 7/20 ---
🔍 Planner analyzing (with UI detection)...
🎯 tap_element → {'text': 'Allow file access'}
📱 Executor: ✓ Tapped at (540, 2016)

--- Step 8/20 ---
🔍 Planner analyzing (with UI detection)...
🎉 Test objective achieved!
💭 SUCCESS! I can see 'Create new note' option - we are inside the vault.
🎯 done → {'result': 'PASS', 'reason': 'Vault created and entered successfully'}

✅ RESULT: PASS
📋 Type: test_passed
⏱️ Duration: 45.2s
```

---

## 10. Lessons Learned

1. **Vision models need explicit guidance**: Even advanced models struggle with coordinate estimation from screenshots. UI Automator integration was essential.

2. **State machines prevent errors**: Forcing action sequences (tap → type → enter) eliminates entire classes of bugs.

3. **Android has many UI quirks**: Stylus popups, permission dialogs, and default text in fields all required specific handling.

4. **Success detection is crucial**: Without knowing when to stop, agents will continue taking random actions indefinitely.

5. **Free APIs are viable**: Groq's free tier provided sufficient quota for development and testing.

---

## 11. Future Improvements

1. **OCR Integration**: Add text recognition to verify typed content appears correctly.

2. **Visual Regression**: Compare screenshots to detect UI changes.

3. **Parallel Execution**: Run multiple test cases simultaneously.

4. **Cross-App Testing**: Extend to test interactions between multiple apps.

5. **Self-Healing Tests**: Automatically adapt when UI elements move.

---

## 12. Conclusion

This project demonstrates that a custom multi-agent system can effectively perform mobile QA testing using freely available tools and APIs. The iterative development process—identifying issues, implementing fixes, and validating solutions—mirrors real-world software engineering practices.

Key achievements:
- Successfully automated vault and note creation in Obsidian
- Handled complex Android UI interactions
- Built robust error detection and recovery mechanisms
- Created a maintainable, extensible codebase

The system serves as both a functional QA tool and a learning platform for understanding multi-agent architectures, vision models, and mobile automation.

---

## References

1. Groq API Documentation: https://console.groq.com/docs
2. Android ADB Documentation: https://developer.android.com/tools/adb
3. UI Automator: https://developer.android.com/training/testing/ui-automator
4. Obsidian Mobile: https://obsidian.md/mobile