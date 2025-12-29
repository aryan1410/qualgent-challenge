# 📱 Mobile QA Agent

## AI-Powered Mobile Application Testing with Vision & Coordinate-Based Automation

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Google ADK](https://img.shields.io/badge/Google%20ADK-0.3+-green.svg)
![Android](https://img.shields.io/badge/Android-ADB-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**An intelligent QA testing agent that can see, understand, and interact with mobile applications autonomously.**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [Metrics](#-metrics)

</div>

---

## 🎯 Project Overview

Mobile QA Agent is an AI-powered testing framework that combines:
- **Vision AI**: Screenshots analyzed by LLMs to understand UI state
- **Coordinate-Based Automation**: Precise UI element interaction via ADB
- **Intelligent Decision Making**: Agent autonomously navigates and tests apps

### What Makes This Different?

| Traditional Automation | Mobile QA Agent |
|----------------------|-----------------|
| Hardcoded element IDs | Vision-based element detection |
| Brittle XPath selectors | Intelligent coordinate extraction |
| Script-based flows | AI-driven decision making |
| Manual test maintenance | Self-adapting to UI changes |

---

## ✨ Features

### 🤖 Smart Agent Capabilities
- **Screenshot Analysis**: Compressed screenshots sent to vision models
- **UI Element Extraction**: Automatic parsing of Android UI hierarchy
- **Intelligent Navigation**: Agent decides next action based on screen state
- **Multi-Step Task Completion**: Complex workflows executed autonomously

### 📊 Comprehensive Metrics
- **Plan Adherence Score**: How closely agent followed ideal workflow
- **Action Efficiency**: Ratio of ideal vs actual steps taken
- **Subgoal Tracking**: Milestone completion monitoring
- **Tool Usage Analytics**: Which tools used and how often

### 🧪 10 Pre-Built Test Cases
1. Create Vault
2. Create Note
3. Verify Appearance Icon Color
4. Find Print to PDF
5. Create Multiple Notes
6. Search Notes
7. Delete Note
8. Change Theme
9. Create Vault with New Folder
10. Link Notes

---

## 🏗 Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        MOBILE QA AGENT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   main.py   │───▶│  agent.py   │───▶│ adb_tools.py│        │
│  │ Test Runner │    │ AI Agent +  │    │   Device    │        │
│  │             │    │  Prompts    │    │ Interaction │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ metrics.py  │    │ Google ADK  │    │Android Device│        │
│  │  Tracking   │    │   + LLM     │    │  /Emulator  │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
mobile-qa-agent/
├── src/
│   ├── main.py                      # 🚀 Entry point & test runner
│   └── mobile_qa_agent/
│       ├── agent.py                 # 🤖 AI agent, tools & prompts
│       └── tools/
│           ├── adb_tools.py         # 📱 ADB commands & UI parsing
│           └── metrics.py           # 📊 Metrics & ideal workflows
├── tests/                           # 🧪 Unit tests
├── results/                         # 📁 Test results output
├── setup.sh                         # ⚙️ Setup script
├── requirements.txt                 # 📦 Dependencies
├── pyproject.toml                   # 📋 Project configuration
└── README.md                        # 📖 This file
```

---

## 🔄 Code Flow & Execution Order

### 1️⃣ Test Execution Flow

```
User runs: python src/main.py --task 1
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│                      main.py                                  │
├──────────────────────────────────────────────────────────────┤
│  1. Parse CLI arguments                                       │
│  2. Load test case from TEST_CASES[1]                        │
│  3. Initialize MobileQARunner                                │
│  4. Check prerequisites (ADB, device)                        │
│  5. If reset_app=True: clear_app_data() + launch_app()       │
│  6. Initialize MetricsTracker                                │
│  7. Call _run_test_with_adk()                               │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│                      agent.py                                 │
├──────────────────────────────────────────────────────────────┤
│  1. create_test_agent() called                               │
│  2. get_test_prompt() selects appropriate prompt             │
│  3. Agent created with tools: [get_screen_elements,          │
│     tap_at_coordinates, tap_element_by_text,                 │
│     type_text_input, press_enter_key, press_back_button,     │
│     swipe_screen]                                            │
│  4. InMemoryRunner executes agent                            │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│                   Agent Loop (ADK)                           │
├──────────────────────────────────────────────────────────────┤
│  REPEAT until "TEST PASSED" or "TEST FAILED" or max_steps:   │
│                                                              │
│  1. Agent calls get_screen_elements()                        │
│     └─▶ adb_tools.py: take_screenshot_compressed()          │
│     └─▶ adb_tools.py: get_ui_hierarchy()                    │
│     └─▶ adb_tools.py: parse_ui_elements()                   │
│     └─▶ Returns: {screenshot_base64, elements, screen_type} │
│                                                              │
│  2. LLM analyzes screenshot + elements                       │
│     └─▶ Decides next action based on prompt instructions    │
│                                                              │
│  3. Agent calls action tool (e.g., tap_at_coordinates)       │
│     └─▶ adb_tools.py: tap(x, y)                             │
│     └─▶ Returns: {success: True, message: "Tapped at..."}   │
│                                                              │
│  4. MetricsTracker.record_step() logs the action             │
│     └─▶ Matches against ideal workflow                       │
│     └─▶ Checks subgoal completion                           │
│     └─▶ Calculates rewards                                  │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│                   Finalization                               │
├──────────────────────────────────────────────────────────────┤
│  1. metrics.finalize() calculates final scores               │
│  2. metrics.print_summary() displays results                 │
│  3. Results saved to results/ directory                      │
└──────────────────────────────────────────────────────────────┘
```

### 2️⃣ Tool Call Flow

```
Agent decides to tap "Create a vault" button
                    │
                    ▼
┌─────────────────────────────────────────┐
│  tap_element_by_text("Create a vault")  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  adb_tools.tap_element(text)            │
│  1. get_ui_hierarchy() - dump XML       │
│  2. parse_ui_elements() - extract nodes │
│  3. Find element matching text          │
│  4. Get center coordinates (x, y)       │
│  5. tap(x, y) - execute ADB tap         │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  ADB Command Executed:                  │
│  adb shell input tap 540 385            │
└─────────────────────────────────────────┘
```

### 3️⃣ Screenshot Processing Flow

```
get_screen_elements() called
            │
            ▼
┌───────────────────────────────────────────────────────────┐
│  take_screenshot_compressed()                              │
├───────────────────────────────────────────────────────────┤
│  1. adb exec-out screencap -p → Raw PNG bytes             │
│  2. PIL.Image.open() → Load image                         │
│  3. Resize: 1080px → 270px width (75% reduction)          │
│  4. Convert PNG → JPEG at 40% quality                     │
│  5. Base64 encode → ~10-20KB string                       │
│  6. Return compressed image for LLM                       │
└───────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────┐
│  get_ui_hierarchy()                                        │
├───────────────────────────────────────────────────────────┤
│  1. adb shell uiautomator dump → XML file on device       │
│  2. adb shell cat → Read XML content                      │
│  3. Return XML string                                     │
└───────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────┐
│  parse_ui_elements(xml)                                    │
├───────────────────────────────────────────────────────────┤
│  1. Regex extract all <node> elements                     │
│  2. For each node, extract:                               │
│     - text, content-desc                                  │
│     - bounds → calculate center (x, y)                    │
│     - class → determine type (button/input/text)          │
│  3. Filter out full-screen containers                     │
│  4. Sort by y-position (top to bottom)                    │
│  5. Return list of UI elements                            │
└───────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────┐
│  Returns to Agent:                                         │
│  {                                                         │
│    "screenshot_base64": "data:image/jpeg;base64,...",     │
│    "elements": [                                           │
│      {"text": "Create a vault", "x": 540, "y": 385, ...}, │
│      {"text": "Use my existing vault", "x": 540, "y": 450}│
│    ],                                                      │
│    "screen_type": "initial_vault_choice"                  │
│  }                                                         │
└───────────────────────────────────────────────────────────┘
```

---

## 📁 File Descriptions

### `src/main.py` - Test Runner & Entry Point

**Purpose**: CLI interface, test case definitions, orchestrates test execution

**Key Components**:
```python
TEST_CASES = {
    1: {
        "name": "Create Vault",
        "description": "...",
        "reset_app": True,      # Clear app data before test
        "success_condition": "...",
        "ground_truth_steps": [...]
    },
    # ... tests 2-10
}

class MobileQARunner:
    def run_test(self, test_number: int) -> dict
    def _run_test_with_adk(self, test: dict, metrics: MetricsTracker)
    def run_all_tests(self) -> dict
```

**When Called**: First file executed, handles CLI arguments

---

### `src/mobile_qa_agent/agent.py` - AI Agent & Prompts

**Purpose**: Defines the intelligent agent, all tools, and task-specific prompts

**Key Components**:
```python
# Tools available to the agent
ALL_TOOLS = [
    get_screen_elements,    # See screen state
    tap_at_coordinates,     # Tap at (x, y)
    tap_element_by_text,    # Find and tap by text
    type_text_input,        # Type into input field
    press_enter_key,        # Press Enter
    press_back_button,      # Navigate back
    swipe_screen           # Scroll up/down
]

# Task-specific prompts
VAULT_CREATION_PROMPT = "..."
NOTE_CREATION_PROMPT = "..."
SEARCH_NOTE_PROMPT = "..."
# ... etc

def get_test_prompt(test_name, test_description, success_condition) -> str
def create_test_agent(test_name, test_description, success_condition, model_name) -> Agent
```

**When Called**: Agent created by main.py for each test

---

### `src/mobile_qa_agent/tools/adb_tools.py` - Device Interaction

**Purpose**: Low-level ADB commands, screenshot capture, UI parsing

**Key Functions**:
```python
# Screenshot
def take_screenshot_compressed(max_width=270, quality=40) -> str

# UI Hierarchy
def get_ui_hierarchy() -> str
def parse_ui_elements(xml: str) -> List[Dict]

# Touch/Input
def tap(x: int, y: int)
def type_text(text: str)
def press_enter()
def press_back()

# App Control
def launch_app(package: str)
def clear_app_data(package: str)
```

**When Called**: By agent tools during test execution

---

### `src/mobile_qa_agent/tools/metrics.py` - Metrics & Ideal Workflows

**Purpose**: Track agent performance, compare against ideal workflows

**Key Components**:
```python
# Ideal workflow for each test
IDEAL_WORKFLOWS = {
    1: {
        "name": "Create Vault",
        "ideal_actions": [
            {"tool": "get_screen_elements", ...},
            {"tool": "tap_element_by_text", "params": {"text": "Create a vault"}, ...},
            # ...
        ],
        "subgoals": ["tap_create_vault", "enter_vault_name", ...]
    },
    # ... tests 2-10
}

class MetricsTracker:
    def start_step(self)
    def record_step(self, action_type, action_params, success, ...)
    def finalize(self, final_result, result_type, reasoning)
    def print_summary(self)
```

**When Called**: Throughout test execution to track every action

---

## 📊 Metrics Explained

### Plan Adherence Score

**What it measures**: How closely the agent followed the ideal workflow

**Calculation**:
```
Plan Adherence = (Matched Ideal Steps / Total Ideal Steps) × 100%
```

**Example**:
- Ideal workflow has 13 steps
- Agent matched 11 of them
- Plan Adherence = 11/13 = **84.6%**

---

### Action Efficiency

**What it measures**: How efficiently the agent completed the task

**Calculation**:
```
Action Efficiency = min(1.0, Ideal Steps / Actual Steps) × 100%
```

**Example**:
- Ideal workflow: 13 steps
- Agent took: 18 steps
- Action Efficiency = 13/18 = **72.2%**

---

### Subgoal Completion Rate

**What it measures**: Percentage of key milestones achieved

**Example Subgoals for Create Vault**:
- ✅ tap_create_vault
- ✅ handle_sync_screen
- ✅ enter_vault_name
- ✅ confirm_vault_creation
- ✅ select_folder
- ❌ handle_permissions (skipped)
- ✅ enter_vault

**Subgoal Completion = 6/7 = 85.7%**

---

### Reward Calculation

```
Total Reward = Step Penalty + Subgoal Rewards + Completion Bonus

Where:
- Step Penalty    = -0.05 per step taken
- Subgoal Reward  = +0.20 per subgoal achieved
- Completion Bonus = +1.00 if test passed
```

**Example**:
```
Steps taken: 15        → Penalty:  -0.75
Subgoals achieved: 6   → Reward:   +1.20
Test passed: Yes       → Bonus:    +1.00
                         ─────────────────
Total Reward:                      +1.45
```

---

### Additional Metrics

| Metric | Description |
|--------|-------------|
| `tool_usage_count` | How many times each tool was called |
| `screen_transitions` | Sequence of screen type changes |
| `error_count` | Number of failed actions |
| `retry_count` | Actions repeated (indicates getting stuck) |
| `duration_seconds` | Total test execution time |
| `average_step_duration` | Average time per action |

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- Android SDK (ADB)
- Android Emulator or physical device
- Google API Key (for Gemini) or OpenAI API Key

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/aryan/mobile-qa-agent.git
cd mobile-qa-agent

# Run setup script
chmod +x setup.sh
./setup.sh

# Configure API key
nano .env  # Add your GOOGLE_API_KEY

# Start Android emulator (or connect device)
emulator -avd Pixel_6_API_34

# Install Obsidian on device
adb install obsidian.apk
```

### Manual Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Create .env file
cp .env.example .env
# Edit .env and add your API key
```

---

## 💻 Usage

### List Available Tests

```bash
python src/main.py --list
```

### Run Single Test

```bash
python src/main.py --task 1          # Run test 1
python src/main.py --task 5          # Run test 5
```

### Run All Tests

```bash
python src/main.py --task all
```

### Disable Metrics

```bash
python src/main.py --task 1 --no-reward
```

---

## 📋 Test Cases Summary

| # | Test Name | Reset | Expected |
|---|-----------|-------|----------|
| 1 | Create Vault | ✅ | PASS |
| 2 | Create Note | ❌ | PASS |
| 3 | Verify Appearance Icon Color | ❌ | FAIL |
| 4 | Find Print to PDF | ❌ | FAIL |
| 5 | Create Multiple Notes | ❌ | PASS |
| 6 | Search Notes | ❌ | PASS |
| 7 | Delete Note | ❌ | PASS |
| 8 | Change Theme | ❌ | PASS |
| 9 | Create Vault with New Folder | ✅ | PASS |
| 10 | Link Notes | ❌ | PASS |

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | One of these |
| `OPENAI_API_KEY` | OpenAI API key | required |
| `TOGETHER_API_KEY` | Together AI key | |
| `APP_PACKAGE` | Target app package | No (default: md.obsidian) |

### Model Selection Priority

1. Together AI (if `TOGETHER_API_KEY` set)
2. OpenAI (if `OPENAI_API_KEY` set)
3. Google Gemini (if `GOOGLE_API_KEY` set)

---

## 📈 Sample Output

```
============================================================
📊 TEST METRICS SUMMARY
============================================================

📋 Test: Create Vault...
🎯 Result: PASS (test_passed)
✓ Matches Expected: True

📈 STEPS:
   Total: 15
   Successful: 15
   Failed: 0
   Errors: 0
   Retries: 1

💰 REWARDS:
   Step Penalty: -0.75
   Subgoal Reward: 1.40
   Completion Bonus: 1.00
   TOTAL REWARD: 1.65

🎯 SUBGOALS:
   Defined: 7
   Achieved: 7
   Completion Rate: 100.0%
   ✓ Completed: tap_create_vault, handle_sync_screen, enter_vault_name, 
                confirm_vault_creation, select_folder, handle_permissions, enter_vault

📐 PLAN ADHERENCE:
   Ideal Steps: 13
   Matched Steps: 12
   Plan Adherence: 92.3%
   Action Efficiency: 86.7%
   Extra Actions: 2
   Missed Actions: 1

🔧 TOOL USAGE:
   get_screen_elements: 8
   tap_element_by_text: 5
   type_text_input: 1
   tap_at_coordinates: 1

⏱️ TIMING:
   Duration: 45.3s
   Avg Step: 3.02s
============================================================
```

---

## 🙏 Acknowledgments

- Built with [Google ADK](https://github.com/google/adk-python)
- Tested on [Obsidian](https://obsidian.md/) mobile app
- Inspired by modern AI agent architectures

---

<div align="center">

**Made with ❤️ for the QualGent Research Challenge**

</div>