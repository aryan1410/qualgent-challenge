# Architecture Documentation

## Overview

The Mobile QA Agent is built using Google's Agent Development Kit (ADK) framework, implementing a multi-agent architecture for automated mobile app testing.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           User Interface                                 │
│                    (CLI / ADK Web / API Server)                         │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        MobileQARunner                                    │
│                   (Test Orchestration Layer)                             │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Google ADK Runtime                                   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                  Root Agent (Orchestrator)                        │   │
│  └───────────────────────────┬───────────────────────────────────────┘   │
│                              │                                           │
│            ┌─────────────────┼─────────────────┐                        │
│            ▼                 ▼                 ▼                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐           │
│  │  PlannerAgent   │ │  ExecutorAgent  │ │ SupervisorAgent │           │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Tool Layer (ADB + Metrics)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Android Device (ADB + UI Automator)                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## Agent Definitions

### Root Agent (Orchestrator)

**Responsibilities:**
- Receives test case instructions from user
- Coordinates workflow between sub-agents
- Manages overall test execution flow
- Reports final results

### Planner Agent

**Responsibilities:**
- Analyzes current screen state using UI Automator
- Decides next action based on test objective
- Handles edge cases (confirmation dialogs, popups)
- Detects test completion or failure conditions

### Supervisor Agent

**Responsibilities:**
- Evaluates final screen state against test objectives
- Determines PASS/FAIL verdict
- Classifies result type
- Generates bug reports when applicable

## Data Flow

### Test Execution Flow

```
1. User Input → "Run test 1"
2. Test Preparation → Clear app, launch, init metrics
3. Agent Loop (max 20 iterations)
   ├── Get Screen State
   ├── Plan Action
   ├── Execute Action
   ├── Record Metrics
   └── Check Completion
4. Finalization → Calculate rewards, save results
```

## Component Details

### ADB Tools Module

| Function | Purpose | ADB Command |
|----------|---------|-------------|
| `take_screenshot()` | Capture screen | `adb exec-out screencap -p` |
| `tap(x, y)` | Tap coordinates | `adb shell input tap x y` |
| `type_text(text)` | Type text | `adb shell input text "..."` |
| `get_ui_hierarchy()` | Get UI XML | `adb shell uiautomator dump` |

### Metrics System

- **Step Penalty**: -0.05 per step
- **Subgoal Reward**: +0.2 per subgoal achieved
- **Completion Bonus**: +1.0 for PASS

## Design Decisions

### Why Google ADK?
- Production-ready framework
- Built-in multi-agent support
- Model flexibility
- Observability tools

### Why UI Automator?
- Accurate element coordinates
- Android native framework
- Reliable across versions

### Why Separate Agents?
- Separation of concerns
- Easy debugging
- Scalability
