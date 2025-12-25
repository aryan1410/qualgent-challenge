"""
Metrics Tracking for Mobile QA Agent
=====================================
Comprehensive metrics and evaluation system for agent performance.
"""

import time
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class StepMetrics:
    """Metrics for a single step in the test."""
    step_number: int
    action_type: str
    action_params: Dict[str, Any]
    timestamp: float
    duration_seconds: float
    success: bool
    
    # Reward components
    base_reward: float = -0.05  # Penalty per step
    subgoal_reward: float = 0.0
    total_step_reward: float = 0.0
    
    # Ground truth comparison
    expected_action: Optional[str] = None
    action_matches_expected: Optional[bool] = None
    relevance_score: float = 0.0  # 0-1 score of how relevant action is
    
    # State info
    screen_type_before: str = ""
    screen_type_after: str = ""
    elements_found: int = 0
    
    # Subgoals
    newly_achieved_subgoals: List[str] = field(default_factory=list)
    cumulative_subgoals: List[str] = field(default_factory=list)


@dataclass
class TestMetrics:
    """Complete metrics for a test case."""
    test_case: str
    test_number: int
    start_time: float
    end_time: float = 0.0
    
    # Results
    final_result: str = ""  # PASS/FAIL
    result_type: str = ""  # test_passed, test_assertion_failed, etc.
    reasoning: str = ""
    bug_report: Optional[str] = None
    
    # Step metrics
    steps: List[StepMetrics] = field(default_factory=list)
    total_steps: int = 0
    successful_steps: int = 0
    failed_steps: int = 0
    
    # Reward metrics
    total_reward: float = 0.0
    step_penalty_total: float = 0.0
    subgoal_reward_total: float = 0.0
    completion_bonus: float = 0.0  # +1.0 if passed
    
    # Efficiency metrics
    duration_seconds: float = 0.0
    average_step_duration: float = 0.0
    
    # Ground truth comparison
    expected_result: str = ""
    matches_expected: bool = False
    ground_truth_plan: List[str] = field(default_factory=list)
    plan_adherence_score: float = 0.0  # How well agent followed expected plan
    
    # Subgoals
    all_subgoals: List[str] = field(default_factory=list)
    achieved_subgoals: List[str] = field(default_factory=list)
    subgoal_completion_rate: float = 0.0


class MetricsTracker:
    """Tracks and calculates metrics during test execution."""
    
    # Reward constants
    STEP_PENALTY = -0.05
    SUBGOAL_REWARD = 0.2
    COMPLETION_BONUS = 1.0
    
    def __init__(self, test_case: str, test_number: int, expected_result: str = "PASS"):
        self.test_metrics = TestMetrics(
            test_case=test_case,
            test_number=test_number,
            start_time=time.time(),
            expected_result=expected_result
        )
        self.current_step = 0
        self.step_start_time = 0.0
        self.achieved_subgoals = set()
        
        # Define subgoals based on test case
        self._define_subgoals()
        
        # Define ground truth plan
        self._define_ground_truth_plan()
    
    def _define_subgoals(self):
        """Define subgoals based on test case."""
        test_lower = self.test_metrics.test_case.lower()
        
        subgoals = []
        
        if 'vault' in test_lower and 'create' in test_lower:
            subgoals = [
                "tap_create_vault",
                "handle_sync_screen",
                "enter_vault_name",
                "confirm_vault_creation",
                "handle_permissions",
                "enter_vault"
            ]
        elif 'note' in test_lower and 'create' in test_lower:
            subgoals = [
                "tap_create_note",
                "enter_note_title",
                "enter_note_content",
                "save_note"
            ]
        elif 'appearance' in test_lower:
            subgoals = [
                "open_settings",
                "find_appearance",
                "verify_icon_color"
            ]
        elif 'print' in test_lower:
            subgoals = [
                "open_menu",
                "search_print_option",
                "verify_print_exists"
            ]
        
        self.test_metrics.all_subgoals = subgoals
    
    def _define_ground_truth_plan(self):
        """Define the expected sequence of actions."""
        test_lower = self.test_metrics.test_case.lower()
        
        plan = []
        
        if 'internvault' in test_lower:
            plan = [
                "tap_element: Create a vault",
                "tap_element: Continue without sync",
                "tap_input: Vault name field",
                "type_text: InternVault",
                "press_enter",
                "tap_element: Create a vault",
                "tap_element: USE THIS FOLDER",
                "tap_element: Allow/ALLOW"
            ]
        elif 'meeting notes' in test_lower:
            plan = [
                "tap_element: Create new note",
                "tap_input: Title field (Untitled)",
                "clear_and_type: Meeting Notes",
                "press_enter",
                "type_text: Daily Standup"
            ]
        
        self.test_metrics.ground_truth_plan = plan
    
    def start_step(self):
        """Start timing a new step."""
        self.current_step += 1
        self.step_start_time = time.time()
    
    def record_step(
        self,
        action_type: str,
        action_params: Dict[str, Any],
        success: bool,
        screen_type_before: str = "",
        screen_type_after: str = "",
        elements_found: int = 0
    ) -> StepMetrics:
        """Record metrics for a completed step."""
        
        duration = time.time() - self.step_start_time
        
        # Calculate base reward (penalty per step)
        base_reward = self.STEP_PENALTY
        
        # Check for subgoal achievements
        newly_achieved = self._check_subgoals(action_type, action_params, screen_type_after)
        subgoal_reward = len(newly_achieved) * self.SUBGOAL_REWARD
        
        # Calculate relevance to ground truth
        relevance_score = self._calculate_relevance(action_type, action_params)
        
        # Check if action matches expected
        expected_action = None
        action_matches = None
        if self.current_step <= len(self.test_metrics.ground_truth_plan):
            expected_action = self.test_metrics.ground_truth_plan[self.current_step - 1]
            action_matches = self._action_matches_expected(action_type, action_params, expected_action)
        
        step_metrics = StepMetrics(
            step_number=self.current_step,
            action_type=action_type,
            action_params=action_params,
            timestamp=time.time(),
            duration_seconds=duration,
            success=success,
            base_reward=base_reward,
            subgoal_reward=subgoal_reward,
            total_step_reward=base_reward + subgoal_reward,
            expected_action=expected_action,
            action_matches_expected=action_matches,
            relevance_score=relevance_score,
            screen_type_before=screen_type_before,
            screen_type_after=screen_type_after,
            elements_found=elements_found,
            newly_achieved_subgoals=list(newly_achieved),
            cumulative_subgoals=list(self.achieved_subgoals)
        )
        
        self.test_metrics.steps.append(step_metrics)
        self.test_metrics.total_steps += 1
        
        if success:
            self.test_metrics.successful_steps += 1
        else:
            self.test_metrics.failed_steps += 1
        
        # Update running totals
        self.test_metrics.step_penalty_total += base_reward
        self.test_metrics.subgoal_reward_total += subgoal_reward
        
        return step_metrics
    
    def _check_subgoals(
        self,
        action_type: str,
        action_params: Dict[str, Any],
        screen_type: str
    ) -> set:
        """Check if any subgoals were achieved by this action."""
        newly_achieved = set()
        
        action_text = str(action_params).lower()
        
        # Map actions to subgoals
        subgoal_triggers = {
            "tap_create_vault": lambda: "create a vault" in action_text or "create vault" in action_text,
            "handle_sync_screen": lambda: "continue without sync" in action_text or "without sync" in action_text,
            "enter_vault_name": lambda: action_type in ["type_text", "clear_and_type"] and "vault" in action_text.lower(),
            "confirm_vault_creation": lambda: "use this folder" in action_text,
            "handle_permissions": lambda: "allow" in action_text,
            "enter_vault": lambda: screen_type == "inside_vault",
            "tap_create_note": lambda: "create new note" in action_text,
            "enter_note_title": lambda: action_type in ["type_text", "clear_and_type"] and "meeting" in action_text,
            "enter_note_content": lambda: "daily" in action_text or "standup" in action_text,
        }
        
        for subgoal in self.test_metrics.all_subgoals:
            if subgoal not in self.achieved_subgoals:
                if subgoal in subgoal_triggers:
                    if subgoal_triggers[subgoal]():
                        newly_achieved.add(subgoal)
                        self.achieved_subgoals.add(subgoal)
        
        return newly_achieved
    
    def _calculate_relevance(self, action_type: str, action_params: Dict[str, Any]) -> float:
        """Calculate how relevant the action is to the test objective."""
        test_lower = self.test_metrics.test_case.lower()
        action_str = f"{action_type}: {action_params}".lower()
        
        # High relevance keywords
        high_relevance = []
        medium_relevance = []
        
        if 'vault' in test_lower:
            high_relevance = ['create', 'vault', 'internvault', 'folder', 'allow', 'sync']
            medium_relevance = ['tap', 'type', 'enter']
        elif 'note' in test_lower:
            high_relevance = ['note', 'meeting', 'daily', 'standup', 'title', 'untitled']
            medium_relevance = ['create', 'tap', 'type']
        
        score = 0.5  # Base score
        
        for keyword in high_relevance:
            if keyword in action_str:
                score += 0.1
        
        for keyword in medium_relevance:
            if keyword in action_str:
                score += 0.05
        
        return min(1.0, score)
    
    def _action_matches_expected(
        self,
        action_type: str,
        action_params: Dict[str, Any],
        expected: str
    ) -> bool:
        """Check if action roughly matches expected action."""
        expected_lower = expected.lower()
        action_str = f"{action_type}: {action_params}".lower()
        
        # Extract key parts
        if ':' in expected_lower:
            expected_type, expected_param = expected_lower.split(':', 1)
            expected_type = expected_type.strip()
            expected_param = expected_param.strip()
            
            # Check type match (flexible)
            type_match = (
                action_type.lower() == expected_type or
                expected_type in action_type.lower() or
                action_type.lower() in expected_type
            )
            
            # Check param match (contains)
            param_match = expected_param in action_str
            
            return type_match and param_match
        
        return expected_lower in action_str
    
    def finalize(self, final_result: str, result_type: str, reasoning: str, bug_report: str = None):
        """Finalize metrics when test completes."""
        self.test_metrics.end_time = time.time()
        self.test_metrics.final_result = final_result
        self.test_metrics.result_type = result_type
        self.test_metrics.reasoning = reasoning
        self.test_metrics.bug_report = bug_report
        
        # Calculate duration
        self.test_metrics.duration_seconds = self.test_metrics.end_time - self.test_metrics.start_time
        
        if self.test_metrics.total_steps > 0:
            self.test_metrics.average_step_duration = (
                self.test_metrics.duration_seconds / self.test_metrics.total_steps
            )
        
        # Completion bonus
        if final_result == "PASS":
            self.test_metrics.completion_bonus = self.COMPLETION_BONUS
        
        # Total reward
        self.test_metrics.total_reward = (
            self.test_metrics.step_penalty_total +
            self.test_metrics.subgoal_reward_total +
            self.test_metrics.completion_bonus
        )
        
        # Check expected result
        self.test_metrics.matches_expected = (
            final_result == self.test_metrics.expected_result
        )
        
        # Subgoal completion rate
        self.test_metrics.achieved_subgoals = list(self.achieved_subgoals)
        if self.test_metrics.all_subgoals:
            self.test_metrics.subgoal_completion_rate = (
                len(self.achieved_subgoals) / len(self.test_metrics.all_subgoals)
            )
        
        # Plan adherence score
        if self.test_metrics.steps:
            matches = sum(
                1 for s in self.test_metrics.steps
                if s.action_matches_expected is True
            )
            self.test_metrics.plan_adherence_score = matches / len(self.test_metrics.steps)
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return asdict(self.test_metrics)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert metrics to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def print_summary(self):
        """Print a summary of the metrics."""
        m = self.test_metrics
        
        print("\n" + "=" * 60)
        print("📊 TEST METRICS SUMMARY")
        print("=" * 60)
        
        print(f"\n📋 Test: {m.test_case[:60]}...")
        print(f"🎯 Result: {m.final_result} ({m.result_type})")
        print(f"✓ Matches Expected: {m.matches_expected}")
        
        print(f"\n📈 STEPS:")
        print(f"   Total: {m.total_steps}")
        print(f"   Successful: {m.successful_steps}")
        print(f"   Failed: {m.failed_steps}")
        
        print(f"\n💰 REWARDS:")
        print(f"   Step Penalty: {m.step_penalty_total:.2f}")
        print(f"   Subgoal Reward: {m.subgoal_reward_total:.2f}")
        print(f"   Completion Bonus: {m.completion_bonus:.2f}")
        print(f"   TOTAL REWARD: {m.total_reward:.2f}")
        
        print(f"\n🎯 SUBGOALS:")
        print(f"   Defined: {len(m.all_subgoals)}")
        print(f"   Achieved: {len(m.achieved_subgoals)}")
        print(f"   Completion Rate: {m.subgoal_completion_rate:.1%}")
        
        print(f"\n📐 GROUND TRUTH:")
        print(f"   Plan Adherence: {m.plan_adherence_score:.1%}")
        
        print(f"\n⏱️ TIMING:")
        print(f"   Duration: {m.duration_seconds:.1f}s")
        print(f"   Avg Step: {m.average_step_duration:.2f}s")
        
        print("=" * 60)


def calculate_reward_from_episode(episode_data: Dict) -> Dict:
    """
    Calculate reward metrics from an episode JSON file.
    
    Args:
        episode_data: Episode data dictionary
    
    Returns:
        Dict: Reward metrics
    """
    steps = episode_data.get('steps', [])
    final_result = episode_data.get('final_result', 'FAIL')
    
    step_penalty = len(steps) * MetricsTracker.STEP_PENALTY
    
    # Count subgoals (simplified)
    subgoal_count = 0
    for step in steps:
        action = step.get('action_type', '')
        if action in ['tap_element', 'type_text', 'clear_and_type']:
            subgoal_count += 1
    
    subgoal_reward = min(subgoal_count, 5) * MetricsTracker.SUBGOAL_REWARD
    
    completion_bonus = MetricsTracker.COMPLETION_BONUS if final_result == 'PASS' else 0
    
    total_reward = step_penalty + subgoal_reward + completion_bonus
    
    return {
        'step_count': len(steps),
        'step_penalty': step_penalty,
        'subgoal_reward': subgoal_reward,
        'completion_bonus': completion_bonus,
        'total_reward': total_reward,
        'final_result': final_result
    }
