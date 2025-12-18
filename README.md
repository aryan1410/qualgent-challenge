# QualGent Mobile QA Multi-Agent System

A multi-agent system for automated mobile QA testing on Android, built for the QualGent Research Intern Coding Challenge.

## Architecture

This system implements a **Supervisor-Planner-Executor** pattern:
```
┌─────────────────────────────────────────────────────────────┐
│                    MobileQAOrchestrator                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Planner    │→ │   Executor   │→ │  Supervisor  │       │
│  │   (Groq)     │  │    (ADB)     │  │    (Groq)    │       │
│  │              │  │              │  │              │       │
│  │ • Analyze    │  │ • tap()      │  │ • Verify     │       │
│  │   screenshot │  │ • swipe()    │  │   results    │       │
│  │ • Decide     │  │ • type()     │  │ • Log final  │       │
│  │   next step  │  │ • etc.       │  │   verdict    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    Android Emulator (via ADB)
```

### Agent Roles

| Agent | Role | LLM-Powered? |
|-------|------|--------------|
| **Planner** | Analyzes screenshots, decides what action to take next | Yes (Groq) |
| **Executor** | Executes ADB commands (tap, swipe, type) | No (deterministic) |
| **Supervisor** | Verifies test completion, determines PASS/FAIL | Yes (Groq) |

## Setup

### 1. Prerequisites
- Python 3.10+
- Android Studio with emulator
- Obsidian APK installed on emulator

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set API Key
```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

Get a free API key at: https://Groq.ai/

### 4. Start Emulator
```bash
emulator -avd YOUR_AVD_NAME -no-snapshot
```

## Usage

### Interactive Mode
```bash
python main.py
```

### Run All Tests
```bash
python main.py --all
```

## Test Cases

| # | Test Case | Expected |
|---|-----------|----------|
| 1 | Create vault "InternVault" and enter | PASS |
| 2 | Create note "Meeting Notes" with "Daily Standup" | PASS |
| 3 | Verify Appearance tab icon is Red | FAIL (it's monochrome) |
| 4 | Find "Print to PDF" button in file menu | FAIL (doesn't exist) |

## Output

Results are saved as JSON with detailed step-by-step information.

### Result Types
- `test_passed`: All assertions verified
- `test_assertion_failed`: Expected condition not met (detected bug)
- `element_not_found`: UI element not found
- `execution_error`: Technical error during execution

## Project Structure
```
qualgent-challenge/
├── main.py           # Entry point
├── agents.py         # Planner, Executor, Supervisor
├── adb_tools.py      # ADB command wrappers
├── prompts.py        # System prompts for each agent
├── report.md         # Framework decision memo
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Demo Video

The demo video shows terminal output alongside the emulator executing all 4 test cases.

## License

MIT License - Created for QualGent Research Intern Challenge