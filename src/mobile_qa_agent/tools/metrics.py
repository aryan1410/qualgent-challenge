"""
Metrics Tracking for Mobile QA Agent
=====================================
Comprehensive metrics and evaluation system for agent performance.
Includes ideal action workflows for plan adherence calculation.
"""

import time
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Set
from datetime import datetime


# =============================================================================
# IDEAL ACTION WORKFLOWS - Based on prompts in agent.py
# =============================================================================

IDEAL_WORKFLOWS = {
    # Test 1: Create Vault
    1: {
        "name": "Create Vault",
        "ideal_actions": [
            {"tool": "get_screen_elements", "description": "Check initial screen"},
            {"tool": "tap_element_by_text", "params": {"text": "Create a vault"}, "description": "Tap Create a vault button"},
            {"tool": "get_screen_elements", "description": "Check sync screen"},
            {"tool": "tap_element_by_text", "params": {"text": "Continue without sync"}, "description": "Skip sync setup"},
            {"tool": "get_screen_elements", "description": "Check vault config screen"},
            {"tool": "type_text_input", "params": {"text": "InternVault"}, "description": "Enter vault name"},
            {"tool": "get_screen_elements", "description": "Verify vault name entered"},
            {"tool": "tap_element_by_text", "params": {"text": "Create a vault"}, "description": "Confirm vault creation"},
            {"tool": "get_screen_elements", "description": "Check file picker"},
            {"tool": "tap_element_by_text", "params": {"text": "USE THIS FOLDER"}, "description": "Select folder"},
            {"tool": "get_screen_elements", "description": "Check for permission dialog"},
            {"tool": "tap_element_by_text", "params": {"text": "Allow"}, "description": "Grant permission"},
            {"tool": "get_screen_elements", "description": "Verify inside vault"},
        ],
        "subgoals": [
            "tap_create_vault",
            "handle_sync_screen", 
            "enter_vault_name",
            "confirm_vault_creation",
            "select_folder",
            "handle_permissions",
            "enter_vault"
        ]
    },
    
    # Test 2: Create Note
    2: {
        "name": "Create Note",
        "ideal_actions": [
            {"tool": "get_screen_elements", "description": "Check vault screen"},
            {"tool": "tap_element_by_text", "params": {"text": "Create new note"}, "description": "Tap create new note"},
            {"tool": "get_screen_elements", "description": "Check note editor"},
            {"tool": "type_text_input", "params": {"text": "Meeting Notes"}, "description": "Enter note title"},
            {"tool": "get_screen_elements", "description": "Verify title entered"},
            {"tool": "type_text_input", "params": {"text": "Daily Standup"}, "description": "Enter note body"},
            {"tool": "get_screen_elements", "description": "Verify note created"},
        ],
        "subgoals": [
            "tap_create_note",
            "enter_note_title",
            "enter_note_content",
            "save_note"
        ]
    },
    
    # Test 3: Verify Appearance Icon Color
    3: {
        "name": "Verify Appearance Icon Color",
        "ideal_actions": [
            {"tool": "get_screen_elements", "description": "Check current screen"},
            {"tool": "tap_at_coordinates", "params": {"x": 100, "y": 128}, "description": "Tap expand/sidebar button"},
            {"tool": "get_screen_elements", "description": "Check sidebar opened"},
            {"tool": "tap_at_coordinates", "params": {"x": 280, "y": 75}, "description": "Tap settings gear icon"},
            {"tool": "get_screen_elements", "description": "Check settings screen"},
            {"tool": "tap_element_by_text", "params": {"text": "Appearance"}, "description": "Tap Appearance option"},
            {"tool": "get_screen_elements", "description": "Verify Appearance settings and check icon color"},
        ],
        "subgoals": [
            "open_sidebar",
            "open_settings",
            "find_appearance",
            "verify_icon_color"
        ]
    },
    
    # Test 4: Find Print to PDF (expected to fail - feature doesn't exist)
    4: {
        "name": "Find Print to PDF",
        "ideal_actions": [
            {"tool": "get_screen_elements", "description": "Check current screen"},
            {"tool": "tap_at_coordinates", "params": {"x": 990, "y": 128}, "description": "Tap three dots menu"},
            {"tool": "get_screen_elements", "description": "Check menu options"},
            {"tool": "swipe_screen", "params": {"direction": "up"}, "description": "Scroll to find Print option"},
            {"tool": "get_screen_elements", "description": "Look for Print to PDF"},
        ],
        "subgoals": [
            "open_menu",
            "search_print_option",
            "verify_print_exists"
        ]
    },
    
    # Test 5: Create Multiple Notes
    5: {
        "name": "Create Multiple Notes",
        "ideal_actions": [
            # Note 1
            {"tool": "get_screen_elements", "description": "Check starting screen (existing note)"},
            {"tool": "tap_at_coordinates", "params": {"x": 600, "y": 2292}, "description": "Tap + icon for new note"},
            {"tool": "get_screen_elements", "description": "Check new note menu"},
            {"tool": "tap_element_by_text", "params": {"text": "Create new note"}, "description": "Tap Create new note"},
            {"tool": "get_screen_elements", "description": "Check note editor"},
            {"tool": "type_text_input", "params": {"text": "Project Ideas"}, "description": "Enter first note title"},
            {"tool": "get_screen_elements", "description": "Verify title"},
            {"tool": "type_text_input", "description": "Enter first note body"},
            {"tool": "get_screen_elements", "description": "Verify first note"},
            {"tool": "tap_at_coordinates", "params": {"x": 540, "y": 129}, "description": "Tap title to restore bottom bar"},
            # Note 2
            {"tool": "get_screen_elements", "description": "Check bottom bar restored"},
            {"tool": "tap_at_coordinates", "params": {"x": 600, "y": 2292}, "description": "Tap + icon for second note"},
            {"tool": "get_screen_elements", "description": "Check new note menu"},
            {"tool": "tap_element_by_text", "params": {"text": "Create new note"}, "description": "Tap Create new note"},
            {"tool": "get_screen_elements", "description": "Check note editor"},
            {"tool": "type_text_input", "params": {"text": "Todo List"}, "description": "Enter second note title"},
            {"tool": "get_screen_elements", "description": "Verify title"},
            {"tool": "type_text_input", "description": "Enter second note body"},
            {"tool": "get_screen_elements", "description": "Verify second note created"},
        ],
        "subgoals": [
            "tap_plus_icon",
            "tap_create_note",
            "enter_note_title",
            "enter_note_content",
            "restore_bottom_bar",
            "create_second_note"
        ]
    },
    
    # Test 6: Search Notes
    6: {
        "name": "Search Notes",
        "ideal_actions": [
            {"tool": "get_screen_elements", "description": "Check current screen"},
            {"tool": "tap_at_coordinates", "params": {"x": 148, "y": 2292}, "description": "Tap search icon"},
            {"tool": "get_screen_elements", "description": "Check search screen"},
            {"tool": "type_text_input", "description": "Type note name to search"},
            {"tool": "get_screen_elements", "description": "Verify search results"},
        ],
        "subgoals": [
            "tap_search_icon",
            "enter_search_query",
            "verify_search_results"
        ]
    },
    
    # Test 7: Delete Note
    7: {
        "name": "Delete Note",
        "ideal_actions": [
            {"tool": "get_screen_elements", "description": "Check current screen"},
            {"tool": "tap_at_coordinates", "params": {"x": 990, "y": 128}, "description": "Tap three dots menu"},
            {"tool": "get_screen_elements", "description": "Check menu options"},
            {"tool": "swipe_screen", "params": {"direction": "up"}, "description": "Scroll to find Delete"},
            {"tool": "get_screen_elements", "description": "Find Delete file option"},
            {"tool": "tap_element_by_text", "params": {"text": "Delete file"}, "description": "Tap Delete file"},
            {"tool": "get_screen_elements", "description": "Verify deletion"},
        ],
        "subgoals": [
            "open_menu",
            "scroll_to_delete",
            "tap_delete",
            "confirm_deletion"
        ]
    },
    
    # Test 8: Change Theme
    8: {
        "name": "Change Theme",
        "ideal_actions": [
            {"tool": "get_screen_elements", "description": "Check current screen"},
            {"tool": "tap_at_coordinates", "params": {"x": 100, "y": 128}, "description": "Tap expand/sidebar button"},
            {"tool": "get_screen_elements", "description": "Check sidebar"},
            {"tool": "tap_at_coordinates", "params": {"x": 280, "y": 75}, "description": "Tap settings gear"},
            {"tool": "get_screen_elements", "description": "Check settings"},
            {"tool": "tap_element_by_text", "params": {"text": "Appearance"}, "description": "Tap Appearance"},
            {"tool": "get_screen_elements", "description": "Check appearance settings"},
            {"tool": "tap_element_by_text", "params": {"text": "Proper Dark"}, "description": "Select dark theme"},
            {"tool": "get_screen_elements", "description": "Verify theme changed"},
            {"tool": "tap_at_coordinates", "params": {"x": 100, "y": 128}, "description": "Tap back to exit"},
        ],
        "subgoals": [
            "open_sidebar",
            "open_settings",
            "open_appearance",
            "select_theme",
            "exit_settings"
        ]
    },
    
    # Test 9: Create Vault with New Folder
    9: {
        "name": "Create Vault with New Folder",
        "ideal_actions": [
            {"tool": "get_screen_elements", "description": "Check initial screen"},
            {"tool": "tap_element_by_text", "params": {"text": "Create a vault"}, "description": "Tap Create a vault"},
            {"tool": "get_screen_elements", "description": "Check sync screen"},
            {"tool": "tap_element_by_text", "params": {"text": "Continue without sync"}, "description": "Skip sync"},
            {"tool": "get_screen_elements", "description": "Check vault config"},
            {"tool": "type_text_input", "params": {"text": "TestVault"}, "description": "Enter vault name"},
            {"tool": "get_screen_elements", "description": "Verify name entered"},
            {"tool": "tap_element_by_text", "params": {"text": "Create a vault"}, "description": "Confirm creation"},
            {"tool": "get_screen_elements", "description": "Check file picker"},
            {"tool": "tap_at_coordinates", "params": {"x": 253, "y": 128}, "description": "Tap new folder icon"},
            {"tool": "get_screen_elements", "description": "Check new folder dialog"},
            {"tool": "type_text_input", "params": {"text": "TestVault"}, "description": "Enter folder name"},
            {"tool": "tap_element_by_text", "params": {"text": "OK"}, "description": "Confirm folder creation"},
            {"tool": "get_screen_elements", "description": "Verify folder created"},
        ],
        "subgoals": [
            "tap_create_vault",
            "handle_sync_screen",
            "enter_vault_name",
            "confirm_vault_creation",
            "tap_new_folder_icon",
            "enter_folder_name",
            "confirm_folder_creation"
        ]
    },
    
    # Test 10: Link Notes
    10: {
        "name": "Link Notes",
        "ideal_actions": [
            {"tool": "get_screen_elements", "description": "Check current note"},
            {"tool": "tap_at_coordinates", "description": "Tap in body area (title_y + 100)"},
            {"tool": "get_screen_elements", "description": "Check editing mode"},
            {"tool": "type_text_input", "params": {"text": "[["}, "description": "Type link syntax"},
            {"tool": "get_screen_elements", "description": "Check for note suggestions"},
            {"tool": "tap_element_by_text", "description": "Tap different note to link"},
            {"tool": "get_screen_elements", "description": "Verify link created"},
        ],
        "subgoals": [
            "position_cursor_in_body",
            "type_link_syntax",
            "select_note_to_link",
            "verify_link_created"
        ]
    }
}


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
    
    # Plan adherence - NEW ENHANCED METRICS
    ideal_workflow: List[Dict] = field(default_factory=list)
    matched_ideal_steps: List[int] = field(default_factory=list)
    plan_adherence_score: float = 0.0  # Percentage of ideal steps matched
    action_efficiency: float = 0.0  # ideal_steps / actual_steps
    extra_actions: int = 0  # Actions beyond ideal workflow
    missed_actions: int = 0  # Ideal actions not performed
    
    # Subgoals
    all_subgoals: List[str] = field(default_factory=list)
    achieved_subgoals: List[str] = field(default_factory=list)
    subgoal_completion_rate: float = 0.0
    
    # Additional metrics
    tool_usage_count: Dict[str, int] = field(default_factory=dict)
    screen_transitions: List[str] = field(default_factory=list)
    error_count: int = 0
    retry_count: int = 0


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
        self.achieved_subgoals: Set[str] = set()
        
        # Load ideal workflow for this test
        self._load_ideal_workflow()
        
        # Track matched ideal steps
        self.matched_ideal_indices: Set[int] = set()
        
        # Track tool usage
        self.tool_usage: Dict[str, int] = {}
        
        # Track screen transitions
        self.last_screen_type = ""
        
        # Track errors and retries
        self.consecutive_same_actions = 0
        self.last_action = ""
    
    def _load_ideal_workflow(self):
        """Load the ideal workflow for this test number."""
        test_num = self.test_metrics.test_number
        
        if test_num in IDEAL_WORKFLOWS:
            workflow = IDEAL_WORKFLOWS[test_num]
            self.test_metrics.ideal_workflow = workflow.get("ideal_actions", [])
            self.test_metrics.all_subgoals = workflow.get("subgoals", [])
        else:
            # Generic workflow if test not defined
            self.test_metrics.ideal_workflow = []
            self.test_metrics.all_subgoals = []
    
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
        
        # Track tool usage
        self.tool_usage[action_type] = self.tool_usage.get(action_type, 0) + 1
        
        # Track screen transitions
        if screen_type_after and screen_type_after != self.last_screen_type:
            self.test_metrics.screen_transitions.append(
                f"{self.last_screen_type} -> {screen_type_after}"
            )
            self.last_screen_type = screen_type_after
        
        # Track retries (same action repeated)
        action_key = f"{action_type}:{action_params}"
        if action_key == self.last_action:
            self.consecutive_same_actions += 1
            if self.consecutive_same_actions >= 2:
                self.test_metrics.retry_count += 1
        else:
            self.consecutive_same_actions = 0
        self.last_action = action_key
        
        # Track errors
        if not success:
            self.test_metrics.error_count += 1
        
        # Calculate base reward (penalty per step)
        base_reward = self.STEP_PENALTY
        
        # Check for subgoal achievements
        newly_achieved = self._check_subgoals(action_type, action_params, screen_type_after)
        subgoal_reward = len(newly_achieved) * self.SUBGOAL_REWARD
        
        # Check if action matches ideal workflow
        matched_idx, matched_action = self._match_ideal_action(action_type, action_params)
        action_matches = matched_idx is not None
        
        # Calculate relevance score
        relevance_score = self._calculate_relevance(action_type, action_params)
        
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
            expected_action=matched_action.get("description") if matched_action else None,
            action_matches_expected=action_matches,
            relevance_score=relevance_score,
            screen_type_before=screen_type_before,
            screen_type_after=screen_type_after,
            elements_found=elements_found,
            newly_achieved_subgoals=list(newly_achieved),
            cumulative_subgoals=list(self.achieved_subgoals)
        )
        
        # Update test metrics
        self.test_metrics.steps.append(step_metrics)
        self.test_metrics.total_steps += 1
        
        if success:
            self.test_metrics.successful_steps += 1
        else:
            self.test_metrics.failed_steps += 1
        
        self.test_metrics.step_penalty_total += base_reward
        self.test_metrics.subgoal_reward_total += subgoal_reward
        
        return step_metrics
    
    def _match_ideal_action(self, action_type: str, action_params: Dict[str, Any]) -> tuple:
        """
        Match an action against the ideal workflow.
        Returns (matched_index, matched_action) or (None, None).
        """
        action_lower = action_type.lower()
        params_str = json.dumps(action_params).lower() if action_params else ""
        
        for idx, ideal_action in enumerate(self.test_metrics.ideal_workflow):
            if idx in self.matched_ideal_indices:
                continue
            
            ideal_tool = ideal_action.get("tool", "").lower()
            ideal_params = ideal_action.get("params", {})
            
            # Check if tool matches
            tool_match = (
                action_lower == ideal_tool or
                action_lower.replace("_", "") == ideal_tool.replace("_", "") or
                # Handle variations
                (action_lower == "tap_at_coordinates" and ideal_tool == "tap_at_coordinates") or
                (action_lower == "tap_element_by_text" and ideal_tool == "tap_element_by_text") or
                (action_lower == "type_text_input" and ideal_tool == "type_text_input") or
                (action_lower == "get_screen_elements" and ideal_tool == "get_screen_elements") or
                (action_lower == "swipe_screen" and ideal_tool == "swipe_screen")
            )
            
            if not tool_match:
                continue
            
            # For get_screen_elements, any call matches
            if ideal_tool == "get_screen_elements":
                self.matched_ideal_indices.add(idx)
                return idx, ideal_action
            
            # Check params match for other tools
            if ideal_params:
                params_match = False
                for key, value in ideal_params.items():
                    if str(value).lower() in params_str:
                        params_match = True
                        break
                
                if params_match:
                    self.matched_ideal_indices.add(idx)
                    return idx, ideal_action
            else:
                # No specific params required, tool match is enough
                self.matched_ideal_indices.add(idx)
                return idx, ideal_action
        
        return None, None
    
    def _check_subgoals(self, action_type: str, action_params: Dict[str, Any], screen_type: str) -> Set[str]:
        """Check if any subgoals were achieved by this action."""
        newly_achieved = set()
        
        action_lower = action_type.lower()
        params_str = json.dumps(action_params).lower() if action_params else ""
        screen_lower = screen_type.lower() if screen_type else ""
        
        # Define subgoal conditions based on test
        subgoal_conditions = {
            # Vault creation subgoals
            "tap_create_vault": lambda: "create a vault" in params_str or "create_vault" in params_str,
            "handle_sync_screen": lambda: "continue without sync" in params_str or "sync" in params_str,
            "enter_vault_name": lambda: action_lower == "type_text_input" and ("vault" in params_str or "intern" in params_str or "test" in params_str),
            "confirm_vault_creation": lambda: "create a vault" in params_str and screen_lower != "initial_vault_choice",
            "select_folder": lambda: "use this folder" in params_str,
            "handle_permissions": lambda: "allow" in params_str,
            "enter_vault": lambda: screen_lower == "inside_vault",
            
            # Note creation subgoals
            "tap_create_note": lambda: "create new note" in params_str,
            "enter_note_title": lambda: action_lower == "type_text_input" and ("meeting" in params_str or "project" in params_str or "todo" in params_str),
            "enter_note_content": lambda: action_lower == "type_text_input" and ("daily" in params_str or "standup" in params_str or len(params_str) > 20),
            "save_note": lambda: screen_lower == "note_editor_with_title",
            
            # Settings/Appearance subgoals
            "open_sidebar": lambda: action_lower == "tap_at_coordinates" and "100" in params_str and "128" in params_str,
            "open_settings": lambda: "settings" in params_str or screen_lower == "settings_screen",
            "find_appearance": lambda: "appearance" in params_str,
            "open_appearance": lambda: "appearance" in params_str,
            "verify_icon_color": lambda: screen_lower == "appearance_settings",
            
            # Search subgoals
            "tap_search_icon": lambda: action_lower == "tap_at_coordinates" and "148" in params_str,
            "enter_search_query": lambda: action_lower == "type_text_input",
            "verify_search_results": lambda: "search" in screen_lower or "find" in params_str,
            
            # Delete subgoals
            "open_menu": lambda: action_lower == "tap_at_coordinates" and "990" in params_str,
            "scroll_to_delete": lambda: action_lower == "swipe_screen",
            "tap_delete": lambda: "delete" in params_str,
            "confirm_deletion": lambda: "delete" in params_str,
            
            # Theme subgoals
            "select_theme": lambda: "dark" in params_str or "theme" in params_str or "proper" in params_str,
            "exit_settings": lambda: action_lower == "tap_at_coordinates" and screen_lower != "settings_screen",
            
            # Multi-note subgoals
            "tap_plus_icon": lambda: action_lower == "tap_at_coordinates" and "600" in params_str and "2292" in params_str,
            "restore_bottom_bar": lambda: action_lower == "tap_at_coordinates" and "540" in params_str and "129" in params_str,
            "create_second_note": lambda: "todo" in params_str or "second" in params_str,
            
            # New folder subgoals
            "tap_new_folder_icon": lambda: action_lower == "tap_at_coordinates" and "253" in params_str,
            "enter_folder_name": lambda: action_lower == "type_text_input" and "test" in params_str,
            "confirm_folder_creation": lambda: "ok" in params_str.lower(),
            
            # Link notes subgoals
            "position_cursor_in_body": lambda: action_lower == "tap_at_coordinates",
            "type_link_syntax": lambda: "[[" in params_str,
            "select_note_to_link": lambda: action_lower == "tap_element_by_text" and ("meeting" in params_str or "project" in params_str),
            "verify_link_created": lambda: screen_lower == "note_editor_with_title",
        }
        
        for subgoal in self.test_metrics.all_subgoals:
            if subgoal in self.achieved_subgoals:
                continue
            
            if subgoal in subgoal_conditions:
                try:
                    if subgoal_conditions[subgoal]():
                        newly_achieved.add(subgoal)
                        self.achieved_subgoals.add(subgoal)
                except:
                    pass
        
        return newly_achieved
    
    def _calculate_relevance(self, action_type: str, action_params: Dict[str, Any]) -> float:
        """Calculate how relevant the action is to the test objective."""
        test_lower = self.test_metrics.test_case.lower()
        action_str = f"{action_type}: {action_params}".lower()
        
        # Skip get_screen_elements for relevance (it's always needed)
        if action_type == "get_screen_elements":
            return 0.5
        
        score = 0.3  # Base score
        
        # High relevance keywords based on test
        relevance_keywords = {
            "vault": ["vault", "create", "folder", "intern", "test", "allow", "sync"],
            "note": ["note", "meeting", "daily", "standup", "title", "create", "project", "todo"],
            "appearance": ["appearance", "settings", "theme", "dark", "color"],
            "search": ["search", "find", "query"],
            "delete": ["delete", "remove", "file"],
            "link": ["link", "[[", "note"],
            "theme": ["theme", "dark", "light", "appearance", "settings"]
        }
        
        for key, keywords in relevance_keywords.items():
            if key in test_lower:
                for kw in keywords:
                    if kw in action_str:
                        score += 0.1
        
        return min(1.0, score)
    
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
        
        # Plan adherence score - percentage of ideal steps matched
        ideal_count = len(self.test_metrics.ideal_workflow)
        if ideal_count > 0:
            self.test_metrics.matched_ideal_steps = list(self.matched_ideal_indices)
            self.test_metrics.plan_adherence_score = len(self.matched_ideal_indices) / ideal_count
            
            # Action efficiency (how close to ideal number of steps)
            if self.test_metrics.total_steps > 0:
                self.test_metrics.action_efficiency = min(1.0, ideal_count / self.test_metrics.total_steps)
            
            # Extra/missed actions
            self.test_metrics.extra_actions = max(0, self.test_metrics.total_steps - ideal_count)
            self.test_metrics.missed_actions = ideal_count - len(self.matched_ideal_indices)
        
        # Store tool usage
        self.test_metrics.tool_usage_count = self.tool_usage
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return asdict(self.test_metrics)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert metrics to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def print_summary(self):
        """Print a comprehensive summary of the metrics."""
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
        print(f"   Errors: {m.error_count}")
        print(f"   Retries: {m.retry_count}")
        
        print(f"\n💰 REWARDS:")
        print(f"   Step Penalty: {m.step_penalty_total:.2f}")
        print(f"   Subgoal Reward: {m.subgoal_reward_total:.2f}")
        print(f"   Completion Bonus: {m.completion_bonus:.2f}")
        print(f"   TOTAL REWARD: {m.total_reward:.2f}")
        
        print(f"\n🎯 SUBGOALS:")
        print(f"   Defined: {len(m.all_subgoals)}")
        print(f"   Achieved: {len(m.achieved_subgoals)}")
        print(f"   Completion Rate: {m.subgoal_completion_rate:.1%}")
        if m.achieved_subgoals:
            print(f"   ✓ Completed: {', '.join(m.achieved_subgoals)}")
        missing = set(m.all_subgoals) - set(m.achieved_subgoals)
        if missing:
            print(f"   ✗ Missing: {', '.join(missing)}")
        
        print(f"\n📐 PLAN ADHERENCE:")
        print(f"   Ideal Steps: {len(m.ideal_workflow)}")
        print(f"   Matched Steps: {len(m.matched_ideal_steps)}")
        print(f"   Plan Adherence: {m.plan_adherence_score:.1%}")
        print(f"   Action Efficiency: {m.action_efficiency:.1%}")
        print(f"   Extra Actions: {m.extra_actions}")
        print(f"   Missed Actions: {m.missed_actions}")
        
        print(f"\n🔧 TOOL USAGE:")
        for tool, count in sorted(m.tool_usage_count.items(), key=lambda x: -x[1]):
            print(f"   {tool}: {count}")
        
        print(f"\n⏱️ TIMING:")
        print(f"   Duration: {m.duration_seconds:.1f}s")
        print(f"   Avg Step: {m.average_step_duration:.2f}s")
        
        if m.screen_transitions:
            print(f"\n🖥️ SCREEN TRANSITIONS:")
            for transition in m.screen_transitions[:5]:
                print(f"   {transition}")
            if len(m.screen_transitions) > 5:
                print(f"   ... and {len(m.screen_transitions) - 5} more")
        
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
        if action in ['tap_element', 'tap_on_element', 'type_text', 'type_in_field', 'clear_and_type', 
                      'tap_at_coordinates', 'tap_element_by_text', 'type_text_input']:
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