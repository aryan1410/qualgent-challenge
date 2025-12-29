# 📊 Metrics and Evaluation System

## Overview

The Mobile QA Agent includes a comprehensive metrics system for measuring agent performance. It tracks every action, compares against ideal workflows, calculates rewards, and provides detailed analytics.

---

## Key Metrics

### 1. Plan Adherence Score

**What it measures**: How closely the agent followed the ideal workflow

**Formula**:
```
Plan Adherence = (Matched Ideal Steps / Total Ideal Steps) × 100%
```

**Example**:
```
Ideal workflow: 13 steps
Agent matched:  11 steps
Plan Adherence: 11/13 = 84.6%
```

**Why it matters**: Higher adherence means the agent is following the expected path, making it easier to debug and predict behavior.

---

### 2. Action Efficiency

**What it measures**: How efficiently the agent completed the task (fewer steps = better)

**Formula**:
```
Action Efficiency = min(1.0, Ideal Steps / Actual Steps) × 100%
```

**Example**:
```
Ideal steps:  13
Actual steps: 18
Efficiency:   13/18 = 72.2%
```

**Interpretation**:
- 100% = Agent used exactly the ideal number of steps
- <100% = Agent took extra steps (exploration, retries, mistakes)
- Capped at 100% (can't be "better than ideal")

---

### 3. Subgoal Completion Rate

**What it measures**: Percentage of key milestones achieved

**Example for Create Vault test**:
```
Subgoals defined:
  ✅ tap_create_vault
  ✅ handle_sync_screen
  ✅ enter_vault_name
  ✅ confirm_vault_creation
  ✅ select_folder
  ❌ handle_permissions (skipped - no dialog appeared)
  ✅ enter_vault

Completion Rate: 6/7 = 85.7%
```

---

### 4. Total Reward

**Formula**:
```
Total Reward = Step Penalty + Subgoal Rewards + Completion Bonus

Where:
  Step Penalty    = -0.05 × number_of_steps
  Subgoal Reward  = +0.20 × subgoals_achieved  
  Completion Bonus = +1.00 if PASS, 0 otherwise
```

**Reward Components**:

| Component | Value | Purpose |
|-----------|-------|---------|
| Step Penalty | -0.05/step | Encourages efficiency |
| Subgoal Reward | +0.20/subgoal | Rewards incremental progress |
| Completion Bonus | +1.00 | Large bonus for success |

---

## Reward Calculation Examples

### Example 1: Successful Efficient Test

```
Test: Create Vault
Steps taken: 10
Subgoals achieved: 7/7
Result: PASS

Calculation:
  Step Penalty:     10 × -0.05 = -0.50
  Subgoal Reward:    7 × +0.20 = +1.40
  Completion Bonus:  1 × +1.00 = +1.00
  ─────────────────────────────────────
  TOTAL REWARD:                = +1.90
```

### Example 2: Successful Inefficient Test

```
Test: Create Note
Steps taken: 25 (many retries)
Subgoals achieved: 4/4
Result: PASS

Calculation:
  Step Penalty:     25 × -0.05 = -1.25
  Subgoal Reward:    4 × +0.20 = +0.80
  Completion Bonus:  1 × +1.00 = +1.00
  ─────────────────────────────────────
  TOTAL REWARD:                = +0.55
```

### Example 3: Failed Test

```
Test: Find Print to PDF
Steps taken: 15
Subgoals achieved: 2/3
Result: FAIL (feature doesn't exist)

Calculation:
  Step Penalty:     15 × -0.05 = -0.75
  Subgoal Reward:    2 × +0.20 = +0.40
  Completion Bonus:  0 × +1.00 = +0.00
  ─────────────────────────────────────
  TOTAL REWARD:                = -0.35
```

---

## Ideal Workflows

Each test has a predefined "ideal" workflow that represents the optimal sequence of actions.

### Test 1: Create Vault

```python
ideal_actions = [
    {"tool": "get_screen_elements", "description": "Check initial screen"},
    {"tool": "tap_element_by_text", "params": {"text": "Create a vault"}},
    {"tool": "get_screen_elements", "description": "Check sync screen"},
    {"tool": "tap_element_by_text", "params": {"text": "Continue without sync"}},
    {"tool": "get_screen_elements", "description": "Check vault config"},
    {"tool": "type_text_input", "params": {"text": "InternVault"}},
    {"tool": "get_screen_elements", "description": "Verify name entered"},
    {"tool": "tap_element_by_text", "params": {"text": "Create a vault"}},
    {"tool": "get_screen_elements", "description": "Check file picker"},
    {"tool": "tap_element_by_text", "params": {"text": "USE THIS FOLDER"}},
    {"tool": "get_screen_elements", "description": "Check permission dialog"},
    {"tool": "tap_element_by_text", "params": {"text": "Allow"}},
    {"tool": "get_screen_elements", "description": "Verify inside vault"},
]

subgoals = [
    "tap_create_vault",
    "handle_sync_screen",
    "enter_vault_name",
    "confirm_vault_creation",
    "select_folder",
    "handle_permissions",
    "enter_vault"
]
```

### Test 5: Create Multiple Notes

```python
ideal_actions = [
    # Note 1
    {"tool": "get_screen_elements"},
    {"tool": "tap_at_coordinates", "params": {"x": 600, "y": 2292}},  # + icon
    {"tool": "get_screen_elements"},
    {"tool": "tap_element_by_text", "params": {"text": "Create new note"}},
    {"tool": "get_screen_elements"},
    {"tool": "type_text_input", "params": {"text": "Project Ideas"}},
    {"tool": "get_screen_elements"},
    {"tool": "type_text_input"},  # Body
    {"tool": "get_screen_elements"},
    {"tool": "tap_at_coordinates", "params": {"x": 540, "y": 129}},  # Restore bar
    # Note 2
    {"tool": "get_screen_elements"},
    {"tool": "tap_at_coordinates", "params": {"x": 600, "y": 2292}},  # + icon
    # ... continues
]

subgoals = [
    "tap_plus_icon",
    "tap_create_note",
    "enter_note_title",
    "enter_note_content",
    "restore_bottom_bar",
    "create_second_note"
]
```

---

## Additional Metrics

### Tool Usage Count

Tracks how many times each tool was called:

```
🔧 TOOL USAGE:
   get_screen_elements: 8
   tap_element_by_text: 5
   type_text_input: 2
   tap_at_coordinates: 1
   swipe_screen: 0
   press_back_button: 0
```

**Insights**:
- High `get_screen_elements` = lots of verification (good)
- High `press_back_button` = navigation issues (concerning)
- High retry of same tool = agent getting stuck

---

### Screen Transitions

Tracks the sequence of screen types:

```
🖥️ SCREEN TRANSITIONS:
   initial_vault_choice -> sync_setup
   sync_setup -> vault_configuration
   vault_configuration -> folder_picker
   folder_picker -> permission_dialog
   permission_dialog -> inside_vault
```

**Useful for**: Understanding navigation flow, debugging stuck states

---

### Error & Retry Counts

```
📈 STEPS:
   Total: 15
   Successful: 14
   Failed: 1
   Errors: 1
   Retries: 2
```

- **Error Count**: Actions that returned failure
- **Retry Count**: Same action repeated consecutively (indicates getting stuck)

---

### Timing Metrics

```
⏱️ TIMING:
   Duration: 45.3s
   Avg Step: 3.02s
```

**Benchmarks**:
- Simple tap: ~1-2s
- Screenshot + analysis: ~2-3s
- Text input: ~3-4s
- Total test: 30-90s typical

---

## Subgoal Detection

Subgoals are automatically detected based on actions and screen state:

```python
subgoal_conditions = {
    # Vault creation
    "tap_create_vault": lambda: "create a vault" in params_str,
    "handle_sync_screen": lambda: "continue without sync" in params_str,
    "enter_vault_name": lambda: action == "type_text_input" and "vault" in params,
    "enter_vault": lambda: screen_type == "inside_vault",
    
    # Note creation
    "tap_create_note": lambda: "create new note" in params_str,
    "enter_note_title": lambda: action == "type_text_input" and title_keyword,
    
    # Settings
    "open_sidebar": lambda: tap at (100, 128),
    "open_settings": lambda: screen_type == "settings_screen",
    
    # etc.
}
```

---

## Output Formats

### Terminal Summary

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

🖥️ SCREEN TRANSITIONS:
   initial_vault_choice -> sync_setup
   sync_setup -> vault_configuration
   ...
============================================================
```

### JSON Output

```json
{
  "test_case": "Create Vault",
  "test_number": 1,
  "final_result": "PASS",
  "result_type": "test_passed",
  "matches_expected": true,
  
  "total_steps": 15,
  "successful_steps": 15,
  "failed_steps": 0,
  "error_count": 0,
  "retry_count": 1,
  
  "total_reward": 1.65,
  "step_penalty_total": -0.75,
  "subgoal_reward_total": 1.40,
  "completion_bonus": 1.00,
  
  "plan_adherence_score": 0.923,
  "action_efficiency": 0.867,
  "extra_actions": 2,
  "missed_actions": 1,
  
  "subgoal_completion_rate": 1.0,
  "achieved_subgoals": ["tap_create_vault", "handle_sync_screen", ...],
  "all_subgoals": ["tap_create_vault", "handle_sync_screen", ...],
  
  "tool_usage_count": {
    "get_screen_elements": 8,
    "tap_element_by_text": 5,
    "type_text_input": 1
  },
  
  "duration_seconds": 45.3,
  "average_step_duration": 3.02,
  
  "screen_transitions": [
    "initial_vault_choice -> sync_setup",
    "sync_setup -> vault_configuration"
  ],
  
  "steps": [
    {
      "step_number": 1,
      "action_type": "get_screen_elements",
      "action_params": {},
      "success": true,
      "duration_seconds": 2.1,
      "base_reward": -0.05,
      "subgoal_reward": 0.0,
      "action_matches_expected": true,
      "screen_type_after": "initial_vault_choice"
    },
    // ... more steps
  ]
}
```

---

## Usage

### Enable/Disable Metrics

```bash
# Default: metrics enabled
python src/main.py --task 1

# Explicitly disable metrics
python src/main.py --task 1 --no-reward
```

### Programmatic Access

```python
from src.mobile_qa_agent.tools.metrics import MetricsTracker, IDEAL_WORKFLOWS

# Initialize tracker
metrics = MetricsTracker(
    test_case="Create Vault",
    test_number=1,
    expected_result="PASS"
)

# Record steps during execution
metrics.start_step()
metrics.record_step(
    action_type="tap_element_by_text",
    action_params={"text": "Create a vault"},
    success=True,
    screen_type_after="sync_setup"
)

# Finalize and get results
metrics.finalize(
    final_result="PASS",
    result_type="test_passed",
    reasoning="Vault created successfully"
)

# Print summary
metrics.print_summary()

# Get as dictionary
results = metrics.to_dict()

# Get as JSON
json_str = metrics.to_json()
```

### Analyze Results

```python
import json

# Load saved results
with open("results/test_1_result.json") as f:
    results = json.load(f)

# Access metrics
print(f"Plan Adherence: {results['plan_adherence_score']:.1%}")
print(f"Action Efficiency: {results['action_efficiency']:.1%}")
print(f"Total Reward: {results['total_reward']:.2f}")
```

---

## Metric Thresholds

Suggested benchmarks for evaluating agent quality:

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Plan Adherence | >90% | 70-90% | <70% |
| Action Efficiency | >80% | 60-80% | <60% |
| Subgoal Completion | 100% | 80-99% | <80% |
| Total Reward | >1.5 | 0.5-1.5 | <0.5 |
| Error Count | 0 | 1-2 | >2 |
| Retry Count | 0-1 | 2-3 | >3 |