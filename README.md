# Mobile QA Agent - QualGent Challenge

A multi-agent system for automated mobile app testing using AI vision models.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  PlannerAgent   │────▶│  ExecutorAgent  │────▶│ SupervisorAgent │
│ (Llama 4 Vision)│     │ (ADB + UI Det)  │     │  (Evaluation)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

- **Planner**: Analyzes screenshots, decides actions
- **Executor**: Runs ADB commands, detects UI elements
- **Supervisor**: Evaluates results, reports bugs

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Get free API key from https://console.groq.com/keys
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# 3. Start emulator with Obsidian installed
adb devices  # verify connected

# 4. Reset Obsidian and run
adb shell pm clear md.obsidian
python main.py
```

## Test Cases

| # | Test | Expected |
|---|------|----------|
| 1 | Create vault 'InternVault' | PASS |
| 2 | Create note 'Meeting Notes' with 'Daily Standup' | PASS |
| 3 | Verify Appearance icon is Red | FAIL (it's purple) |
| 4 | Find 'Print to PDF' button | FAIL (doesn't exist) |

## Usage

```bash
python main.py           # Interactive menu
python main.py --all     # Run all tests
python main.py --test 1  # Run specific test
```

## Key Features

- **UI Automator Integration**: Gets exact element coordinates (no guessing)
- **State Machine**: Enforces tap → type → enter sequences
- **Success Detection**: Knows when test objective is achieved
- **Auto-Fixes**: Handles stylus popups, clears existing text, prioritizes buttons

## Files

```
├── main.py          # Entry point
├── agents.py        # Three agents
├── adb_tools.py     # ADB + UI detection
├── prompts.py       # Agent prompts
├── report.md        # Detailed technical report
└── requirements.txt # Dependencies
```

## Reset Obsidian

```bash
adb shell pm clear md.obsidian
```

## Requirements

- Python 3.10+
- Android emulator with Obsidian installed
- Groq API key (free)

See `report.md` for detailed technical documentation.