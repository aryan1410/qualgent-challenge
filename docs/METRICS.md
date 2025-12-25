# Metrics and Evaluation System

## Overview

The Mobile QA Agent includes a comprehensive metrics and evaluation system for measuring agent performance. This system tracks step-by-step actions, calculates rewards, and compares against ground truth plans.

## Reward Function

### Formula

```
Total Reward = Step Penalty + Subgoal Reward + Completion Bonus

Where:
- Step Penalty = -0.05 × number_of_steps
- Subgoal Reward = +0.2 × subgoals_achieved  
- Completion Bonus = +1.0 if PASS, 0 otherwise
```

### Rationale

| Component | Value | Purpose |
|-----------|-------|---------|
| Step Penalty | -0.05 | Encourages efficiency - fewer steps = higher reward |
| Subgoal Reward | +0.2 | Rewards progress toward objective |
| Completion Bonus | +1.0 | Large bonus for successful completion |

### Example Calculations

**Successful Test (8 steps, 5 subgoals):**
```
Step Penalty:    8 × -0.05 = -0.40
Subgoal Reward:  5 × +0.20 = +1.00
Completion:      1 × +1.00 = +1.00
─────────────────────────────────────
TOTAL REWARD:              = +1.60
```

**Failed Test (15 steps, 3 subgoals):**
```
Step Penalty:    15 × -0.05 = -0.75
Subgoal Reward:   3 × +0.20 = +0.60
Completion:       0 × +1.00 = +0.00
─────────────────────────────────────
TOTAL REWARD:               = -0.15
```

## Metrics Tracked

### Per-Step Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `step_number` | int | Sequential step count |
| `action_type` | str | Type of action (tap_element, type_text, etc.) |
| `action_params` | dict | Parameters passed to action |
| `timestamp` | float | Unix timestamp |
| `duration_seconds` | float | Time to execute step |
| `success` | bool | Whether action succeeded |
| `base_reward` | float | Step penalty (-0.05) |
| `subgoal_reward` | float | Subgoal achievement bonus |
| `total_step_reward` | float | Sum of rewards for step |
| `relevance_score` | float | 0-1 score of action relevance |
| `action_matches_expected` | bool | Does action match ground truth? |
| `screen_type_before` | str | Screen state before action |
| `screen_type_after` | str | Screen state after action |

### Per-Test Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `test_case` | str | Test description |
| `test_number` | int | Test ID |
| `final_result` | str | PASS or FAIL |
| `result_type` | str | Classification of result |
| `total_steps` | int | Number of steps taken |
| `successful_steps` | int | Steps that succeeded |
| `failed_steps` | int | Steps that failed |
| `total_reward` | float | Final reward score |
| `duration_seconds` | float | Total test duration |
| `subgoal_completion_rate` | float | % of subgoals achieved |
| `plan_adherence_score` | float | % match with ground truth |

## Subgoal Detection

### Automatic Subgoal Tracking

The system automatically detects when intermediate objectives are achieved based on actions and screen state.

**Test 1 (Create Vault) Subgoals:**
```python
subgoals = [
    "tap_create_vault",      # Tap initial Create a vault button
    "handle_sync_screen",    # Handle sync options
    "enter_vault_name",      # Enter InternVault
    "confirm_vault_creation", # Tap USE THIS FOLDER
    "handle_permissions",    # Grant file permissions
    "enter_vault"            # Successfully enter vault
]
```

**Detection Logic:**
```python
def _check_subgoals(self, action_type, action_params, screen_type):
    subgoal_triggers = {
        "tap_create_vault": lambda: "create a vault" in action_text,
        "enter_vault_name": lambda: action_type == "type_text" and "vault" in text,
        "enter_vault": lambda: screen_type == "inside_vault",
        # ...
    }
```

## Ground Truth Comparison

### Plan Adherence Score

Measures how closely the agent follows the expected sequence of actions.

**Ground Truth Plan Example:**
```python
ground_truth_plan = [
    "tap_element: Create a vault",
    "tap_element: Continue without sync",
    "tap_input: Vault name",
    "clear_and_type: InternVault",
    "press_enter",
    "tap_element: Create a vault",
    "tap_element: USE THIS FOLDER",
    "tap_element: Allow"
]
```

**Calculation:**
```
Plan Adherence = (actions matching expected) / (total actions)
```

### Relevance Score

Measures how relevant each action is to the test objective.

**Scoring:**
```python
score = 0.5  # Base score

# High relevance keywords add +0.1 each
for keyword in ['create', 'vault', 'internvault', 'folder', 'allow']:
    if keyword in action_str:
        score += 0.1

# Medium relevance keywords add +0.05 each
for keyword in ['tap', 'type', 'enter']:
    if keyword in action_str:
        score += 0.05

return min(1.0, score)
```

## Output Format

### JSON Episode File

```json
{
  "test_case": "Open Obsidian, create a new Vault named 'InternVault'...",
  "test_number": 1,
  "start_time": 1703520000.0,
  "end_time": 1703520045.2,
  "final_result": "PASS",
  "result_type": "test_passed",
  "reasoning": "Vault created and entered successfully",
  "total_steps": 8,
  "successful_steps": 8,
  "failed_steps": 0,
  "total_reward": 1.60,
  "step_penalty_total": -0.40,
  "subgoal_reward_total": 1.00,
  "completion_bonus": 1.00,
  "duration_seconds": 45.2,
  "average_step_duration": 5.65,
  "subgoal_completion_rate": 1.0,
  "plan_adherence_score": 0.875,
  "achieved_subgoals": [
    "tap_create_vault",
    "handle_sync_screen",
    "enter_vault_name",
    "confirm_vault_creation",
    "handle_permissions",
    "enter_vault"
  ],
  "steps": [
    {
      "step_number": 1,
      "action_type": "tap_element",
      "action_params": {"text": "Create a vault"},
      "timestamp": 1703520005.0,
      "duration_seconds": 3.2,
      "success": true,
      "base_reward": -0.05,
      "subgoal_reward": 0.2,
      "total_step_reward": 0.15,
      "relevance_score": 0.9,
      "action_matches_expected": true,
      "newly_achieved_subgoals": ["tap_create_vault"]
    }
    // ... more steps
  ]
}
```

### Terminal Summary

```
============================================================
📊 TEST METRICS SUMMARY
============================================================

📋 Test: Create a new Vault named 'InternVault'...
🎯 Result: PASS (test_passed)
✓ Matches Expected: True

📈 STEPS:
   Total: 8
   Successful: 8
   Failed: 0

💰 REWARDS:
   Step Penalty: -0.40
   Subgoal Reward: 1.00
   Completion Bonus: 1.00
   TOTAL REWARD: 1.60

🎯 SUBGOALS:
   Defined: 6
   Achieved: 6
   Completion Rate: 100.0%

📐 GROUND TRUTH:
   Plan Adherence: 87.5%

⏱️ TIMING:
   Duration: 45.2s
   Avg Step: 5.65s
============================================================
```

## Usage

### Enable Metrics During Test Run

```bash
# Default: metrics enabled
python -m src.main --task 1

# Explicit enable
python -m src.main --task 1 --calculate-reward

# Disable metrics
python -m src.main --task 1 --no-reward
```

### Analyze Existing Results

```python
from mobile_qa_agent.tools.metrics import calculate_reward_from_episode
import json

# Load episode
with open('results/test_1_20231225.json') as f:
    episode = json.load(f)

# Calculate rewards
rewards = calculate_reward_from_episode(episode)
print(f"Total Reward: {rewards['total_reward']}")
```

### Batch Analysis

```bash
# Analyze all results in directory
python scripts/analyze_results.py results/*.json

# Generate comparison report
python scripts/compare_runs.py results/run1/ results/run2/
```

## Extending Metrics

### Adding Custom Metrics

```python
class CustomMetricsTracker(MetricsTracker):
    
    def record_step(self, ...):
        step_metrics = super().record_step(...)
        
        # Add custom metric
        step_metrics.custom_metric = self.calculate_custom(...)
        
        return step_metrics
    
    def calculate_custom(self):
        # Custom calculation
        return value
```

### Adding New Subgoals

```python
def _define_subgoals(self):
    if 'custom_test' in self.test_metrics.test_case.lower():
        self.test_metrics.all_subgoals = [
            "custom_subgoal_1",
            "custom_subgoal_2",
            # ...
        ]
```
