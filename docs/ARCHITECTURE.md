# 🏗️ Architecture Documentation

## Overview

The Mobile QA Agent is an AI-powered testing framework built using Google's Agent Development Kit (ADK). It combines vision-based screen understanding with coordinate-based UI automation to test mobile applications autonomously.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER                                        │
│                     python src/main.py --task 1                         │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           main.py                                        │
│                    (CLI & Test Orchestration)                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  • Parse CLI arguments                                          │    │
│  │  • Load TEST_CASES configuration                                │    │
│  │  • Initialize MobileQARunner                                    │    │
│  │  • Reset app if needed (clear_app_data + launch_app)           │    │
│  │  • Initialize MetricsTracker                                    │    │
│  │  • Execute test with ADK                                        │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           agent.py                                       │
│                    (AI Agent & Tool Definitions)                        │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  create_test_agent()                                            │    │
│  │  ├── get_test_prompt() → Select task-specific prompt           │    │
│  │  ├── ALL_TOOLS → [get_screen_elements, tap_at_coordinates,     │    │
│  │  │                tap_element_by_text, type_text_input,        │    │
│  │  │                press_enter_key, press_back_button,          │    │
│  │  │                swipe_screen]                                 │    │
│  │  └── Return configured Agent instance                          │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Google ADK Runtime                                │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  InMemoryRunner                                                 │    │
│  │  ├── Creates session                                            │    │
│  │  ├── Sends initial prompt to LLM                               │    │
│  │  └── Executes agent loop:                                       │    │
│  │      ┌─────────────────────────────────────────────────────┐   │    │
│  │      │  LOOP until "TEST PASSED" or "TEST FAILED":         │   │    │
│  │      │  1. LLM decides next action                         │   │    │
│  │      │  2. Tool function called                            │   │    │
│  │      │  3. Result returned to LLM                          │   │    │
│  │      │  4. Metrics recorded                                │   │    │
│  │      └─────────────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         adb_tools.py                                     │
│                    (Device Interaction Layer)                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Screenshot:                                                    │    │
│  │  └── take_screenshot_compressed() → JPEG base64 (~15KB)        │    │
│  │                                                                 │    │
│  │  UI Hierarchy:                                                  │    │
│  │  ├── get_ui_hierarchy() → XML dump                             │    │
│  │  └── parse_ui_elements() → [{text, x, y, type}, ...]          │    │
│  │                                                                 │    │
│  │  Actions:                                                       │    │
│  │  ├── tap(x, y)                                                 │    │
│  │  ├── type_text(text)                                           │    │
│  │  ├── press_enter() / press_back()                              │    │
│  │  └── clear_and_type(x, y, text)                                │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Android Device / Emulator                           │
│                         (via ADB connection)                            │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  • Obsidian App (md.obsidian)                                   │    │
│  │  • UI Automator service                                         │    │
│  │  • Input injection                                              │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. main.py - Test Runner & Entry Point

**Purpose**: CLI interface, test case definitions, orchestrates test execution

**Key Classes & Functions**:

```python
TEST_CASES = {
    1: {
        "name": "Create Vault",
        "description": "...",
        "reset_app": True,           # Clear app data before test
        "expected_result": "PASS",
        "success_condition": "...",
        "ground_truth_steps": [...]
    },
    # ... tests 2-10
}

class MobileQARunner:
    def __init__(self, calculate_reward=True, verbose=True)
    def check_prerequisites(self) -> bool      # Verify ADB, device
    def run_test(self, test_number: int) -> dict
    async def _run_test_with_adk(self, test: dict, metrics: MetricsTracker)
    def run_all_tests(self) -> dict
```

**Execution Flow**:
1. Parse CLI arguments (`--task`, `--list`, `--no-reward`)
2. Load test configuration from `TEST_CASES`
3. Check prerequisites (ADB connected, device available)
4. If `reset_app=True`: clear app data and relaunch
5. Initialize `MetricsTracker` with test info
6. Create agent via `create_test_agent()`
7. Run agent loop via ADK `InMemoryRunner`
8. Finalize metrics and save results

---

### 2. agent.py - AI Agent & Prompts

**Purpose**: Defines the intelligent agent, all available tools, and task-specific prompts

**Key Components**:

```python
# Available tools for the agent
ALL_TOOLS = [
    get_screen_elements,    # Returns screenshot + UI elements
    tap_at_coordinates,     # Tap at (x, y) coordinates
    tap_element_by_text,    # Find element by text and tap
    type_text_input,        # Tap input field and type text
    press_enter_key,        # Press Enter key
    press_back_button,      # Press Back button
    swipe_screen           # Swipe up/down for scrolling
]

# Task-specific prompts
VAULT_CREATION_PROMPT = "..."
NOTE_CREATION_PROMPT = "..."
MULTI_NOTE_CREATION_PROMPT = "..."
SEARCH_NOTE_PROMPT = "..."
DELETE_NOTE_PROMPT = "..."
LINK_NOTES_PROMPT = "..."
SETTINGS_NAVIGATION_PROMPT = "..."
CHANGE_THEME_PROMPT = "..."
CREATE_VAULT_NEW_FOLDER_PROMPT = "..."
GENERIC_TEST_PROMPT = "..."

def get_test_prompt(test_name, test_description, success_condition) -> str
def create_test_agent(test_name, test_description, success_condition, model_name) -> Agent
```

**Prompt Selection Logic**:
```python
def get_test_prompt(test_name, test_description, success_condition):
    # Priority-based prompt selection
    if "link" in description:       → LINK_NOTES_PROMPT
    elif "theme" in description:    → CHANGE_THEME_PROMPT
    elif "delete" in description:   → DELETE_NOTE_PROMPT
    elif "search" in description:   → SEARCH_NOTE_PROMPT
    elif "multiple notes":          → MULTI_NOTE_CREATION_PROMPT
    elif "vault" + "folder":        → CREATE_VAULT_NEW_FOLDER_PROMPT
    elif "vault" + "create":        → VAULT_CREATION_PROMPT
    elif "note" + "create":         → NOTE_CREATION_PROMPT
    elif "appearance"/"settings":   → SETTINGS_NAVIGATION_PROMPT
    else:                           → GENERIC_TEST_PROMPT
```

---

### 3. adb_tools.py - Device Interaction

**Purpose**: Low-level ADB commands, screenshot capture, UI hierarchy parsing

**Key Functions**:

| Function | Purpose | ADB Command |
|----------|---------|-------------|
| `take_screenshot_compressed()` | Capture & compress screen | `adb exec-out screencap -p` |
| `get_ui_hierarchy()` | Dump UI XML | `adb shell uiautomator dump` |
| `parse_ui_elements(xml)` | Extract element info | (XML parsing) |
| `tap(x, y)` | Tap at coordinates | `adb shell input tap x y` |
| `type_text(text)` | Type text | `adb shell input text "..."` |
| `press_enter()` | Press Enter | `adb shell input keyevent 66` |
| `press_back()` | Press Back | `adb shell input keyevent 4` |
| `tap_element(text)` | Find & tap by text | (hierarchy + tap) |
| `clear_app_data(package)` | Reset app | `adb shell pm clear` |
| `launch_app(package)` | Start app | `adb shell monkey -p ...` |

**Screenshot Compression Pipeline**:
```
1. adb exec-out screencap -p     → Raw PNG (~2MB)
2. PIL.Image.open()              → Load image
3. Resize 1080px → 270px         → 75% size reduction
4. Convert PNG → JPEG @ 40%      → Lossy compression
5. Base64 encode                 → ~15KB string for LLM
```

---

### 4. metrics.py - Performance Tracking

**Purpose**: Track agent performance, compare against ideal workflows, calculate rewards

**Key Components**:

```python
# Ideal workflows for all 10 tests
IDEAL_WORKFLOWS = {
    1: {
        "name": "Create Vault",
        "ideal_actions": [...],
        "subgoals": [...]
    },
    # ... tests 2-10
}

@dataclass
class StepMetrics:
    step_number: int
    action_type: str
    action_params: Dict
    success: bool
    base_reward: float
    subgoal_reward: float
    # ... more fields

@dataclass  
class TestMetrics:
    test_case: str
    final_result: str
    plan_adherence_score: float
    action_efficiency: float
    # ... more fields

class MetricsTracker:
    def start_step(self)
    def record_step(self, action_type, action_params, success, ...)
    def finalize(self, final_result, result_type, reasoning)
    def print_summary(self)
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AGENT EXECUTION LOOP                            │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │  LLM Model   │ ◄─────────────────────────────────────────────┐
    │  (Gemini/    │                                                │
    │   GPT-4o)    │                                                │
    └──────┬───────┘                                                │
           │                                                        │
           │ 1. Decides action based on                            │
           │    - Current screenshot                                │
           │    - UI elements list                                  │
           │    - Task prompt                                       │
           │                                                        │
           ▼                                                        │
    ┌──────────────┐                                                │
    │  Tool Call   │                                                │
    │  e.g., tap_  │                                                │
    │  at_coords   │                                                │
    └──────┬───────┘                                                │
           │                                                        │
           │ 2. Execute tool                                        │
           ▼                                                        │
    ┌──────────────┐     ┌──────────────┐                          │
    │  adb_tools   │────▶│   Android    │                          │
    │  functions   │◄────│   Device     │                          │
    └──────┬───────┘     └──────────────┘                          │
           │                                                        │
           │ 3. Return result                                       │
           ▼                                                        │
    ┌──────────────┐                                                │
    │   Metrics    │                                                │
    │   Tracker    │                                                │
    └──────┬───────┘                                                │
           │                                                        │
           │ 4. Record step, check subgoals                        │
           │                                                        │
           ▼                                                        │
    ┌──────────────┐                                                │
    │  Tool Result │ ───────────────────────────────────────────────┘
    │  + Updated   │     5. Send result back to LLM
    │  Screen Info │        for next decision
    └──────────────┘
```

---

## Design Decisions

### Why Google ADK?

| Feature | Benefit |
|---------|---------|
| Production-ready | Stable, well-tested framework |
| Multi-model support | Works with Gemini, GPT-4o, Llama, etc. |
| Built-in tool calling | Native function calling support |
| Async execution | Efficient handling of I/O operations |
| Observability | Easy debugging and logging |

### Why Vision + Coordinates?

| Approach | Pros | Cons |
|----------|------|------|
| **Vision-based** | Sees icons, colors, layout | Can't get exact coordinates |
| **UI Hierarchy** | Exact coordinates | Misses visual elements |
| **Combined** ✓ | Best of both worlds | Slightly more complex |

Our approach:
1. Screenshot shows the LLM what the screen looks like
2. UI hierarchy provides exact tap coordinates
3. Agent uses visual understanding to decide WHAT to do
4. Agent uses coordinates to do it PRECISELY

### Why Screenshot Compression?

| Format | Size | Tokens |
|--------|------|--------|
| Raw PNG | ~2MB | ~170K |
| Compressed JPEG | ~15KB | ~2K |

Without compression, a single screenshot would exceed most context windows. Our 270px wide JPEG at 40% quality provides enough detail for UI understanding while staying under token limits.

### Why Task-Specific Prompts?

Generic prompts lead to:
- More exploration steps
- Higher chance of getting stuck
- Lower success rates

Task-specific prompts provide:
- Exact coordinates for known UI elements
- Step-by-step guidance
- Recovery instructions for common issues

---

## Model Support

The agent supports multiple LLM providers:

| Provider | Model | Environment Variable |
|----------|-------|---------------------|
| Google | Gemini 2.0 Flash | `GOOGLE_API_KEY` |
| OpenAI | GPT-4o-mini | `OPENAI_API_KEY` |
| Together AI | Llama 3.3 70B | `TOGETHER_API_KEY` |

Selection priority (in `main.py`):
```python
if together_key:
    model = "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo"
elif openai_key:
    model = "openai/gpt-4o-mini"
elif google_key:
    model = "gemini-2.0-flash"
```

---

## File Structure

```
mobile-qa-agent/
├── src/
│   ├── __init__.py
│   ├── main.py                          # Entry point, test runner
│   └── mobile_qa_agent/
│       ├── __init__.py
│       ├── agent.py                     # Agent, tools, prompts
│       └── tools/
│           ├── __init__.py
│           ├── adb_tools.py             # ADB commands, UI parsing
│           └── metrics.py               # Metrics, ideal workflows
├── tests/                               # Unit tests
├── results/                             # Test output directory
├── docs/                                # Documentation
│   ├── ARCHITECTURE.md                  # This file
│   ├── METRICS.md                       # Metrics documentation
│   └── TOOLS.md                         # Tool reference
├── setup.sh                             # Setup script
├── verify_framework.py                  # Installation verification
├── requirements.txt                     # Dependencies
├── pyproject.toml                       # Project configuration
└── README.md                            # Main documentation
```