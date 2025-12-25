"""
Tests for the Metrics module.
"""

import pytest
import json
import time
from src.mobile_qa_agent.tools.metrics import (
    MetricsTracker,
    StepMetrics,
    TestMetrics,
    calculate_reward_from_episode
)


class TestMetricsTracker:
    """Test MetricsTracker class."""
    
    def test_initialization(self):
        """Test MetricsTracker initialization."""
        tracker = MetricsTracker(
            test_case="Test case description",
            test_number=1,
            expected_result="PASS"
        )
        
        assert tracker.test_metrics.test_case == "Test case description"
        assert tracker.test_metrics.test_number == 1
        assert tracker.test_metrics.expected_result == "PASS"
        assert tracker.current_step == 0
    
    def test_subgoal_definition(self):
        """Test automatic subgoal definition for vault test."""
        tracker = MetricsTracker(
            test_case="Create a new Vault named 'InternVault'",
            test_number=1,
            expected_result="PASS"
        )
        
        assert len(tracker.test_metrics.all_subgoals) > 0
        assert "tap_create_vault" in tracker.test_metrics.all_subgoals
    
    def test_ground_truth_definition(self):
        """Test ground truth plan definition."""
        tracker = MetricsTracker(
            test_case="Create vault InternVault",
            test_number=1,
            expected_result="PASS"
        )
        
        assert len(tracker.test_metrics.ground_truth_plan) > 0
    
    def test_record_step(self):
        """Test recording a step."""
        tracker = MetricsTracker(
            test_case="Test case",
            test_number=1,
            expected_result="PASS"
        )
        
        tracker.start_step()
        time.sleep(0.1)  # Simulate some work
        
        step = tracker.record_step(
            action_type="tap_element",
            action_params={"text": "Button"},
            success=True,
            screen_type_before="initial",
            screen_type_after="next"
        )
        
        assert step.step_number == 1
        assert step.action_type == "tap_element"
        assert step.success == True
        assert step.base_reward == -0.05
        assert step.duration_seconds >= 0.1
    
    def test_reward_calculation(self):
        """Test reward calculation."""
        tracker = MetricsTracker(
            test_case="Test",
            test_number=1,
            expected_result="PASS"
        )
        
        # Simulate 5 steps
        for i in range(5):
            tracker.start_step()
            tracker.record_step(
                action_type="tap_element",
                action_params={"text": f"Button {i}"},
                success=True
            )
        
        tracker.finalize(
            final_result="PASS",
            result_type="test_passed",
            reasoning="Test completed"
        )
        
        metrics = tracker.test_metrics
        
        # 5 steps × -0.05 = -0.25
        assert metrics.step_penalty_total == pytest.approx(-0.25, abs=0.01)
        
        # Completion bonus for PASS
        assert metrics.completion_bonus == 1.0
        
        # Total should be penalty + subgoals + completion
        assert metrics.total_reward == pytest.approx(
            metrics.step_penalty_total + 
            metrics.subgoal_reward_total + 
            metrics.completion_bonus,
            abs=0.01
        )
    
    def test_fail_no_completion_bonus(self):
        """Test that FAIL results don't get completion bonus."""
        tracker = MetricsTracker(
            test_case="Test",
            test_number=1,
            expected_result="PASS"
        )
        
        tracker.start_step()
        tracker.record_step(
            action_type="tap_element",
            action_params={"text": "Button"},
            success=False
        )
        
        tracker.finalize(
            final_result="FAIL",
            result_type="execution_error",
            reasoning="Test failed"
        )
        
        assert tracker.test_metrics.completion_bonus == 0.0
    
    def test_matches_expected(self):
        """Test expected result matching."""
        tracker = MetricsTracker(
            test_case="Test",
            test_number=1,
            expected_result="PASS"
        )
        
        tracker.finalize("PASS", "test_passed", "Done")
        assert tracker.test_metrics.matches_expected == True
        
        tracker2 = MetricsTracker(
            test_case="Test",
            test_number=2,
            expected_result="PASS"
        )
        
        tracker2.finalize("FAIL", "execution_error", "Failed")
        assert tracker2.test_metrics.matches_expected == False
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        tracker = MetricsTracker(
            test_case="Test",
            test_number=1,
            expected_result="PASS"
        )
        
        tracker.finalize("PASS", "test_passed", "Done")
        
        data = tracker.to_dict()
        
        assert isinstance(data, dict)
        assert data["test_case"] == "Test"
        assert data["final_result"] == "PASS"
    
    def test_to_json(self):
        """Test conversion to JSON."""
        tracker = MetricsTracker(
            test_case="Test",
            test_number=1,
            expected_result="PASS"
        )
        
        tracker.finalize("PASS", "test_passed", "Done")
        
        json_str = tracker.to_json()
        
        # Should be valid JSON
        data = json.loads(json_str)
        assert data["test_case"] == "Test"


class TestRelevanceScore:
    """Test relevance score calculation."""
    
    def test_high_relevance(self):
        """Test high relevance actions."""
        tracker = MetricsTracker(
            test_case="Create vault InternVault",
            test_number=1,
            expected_result="PASS"
        )
        
        score = tracker._calculate_relevance(
            "tap_element",
            {"text": "Create a vault"}
        )
        
        # Should be high relevance
        assert score > 0.7
    
    def test_low_relevance(self):
        """Test low relevance actions."""
        tracker = MetricsTracker(
            test_case="Create vault",
            test_number=1,
            expected_result="PASS"
        )
        
        score = tracker._calculate_relevance(
            "swipe",
            {"start_x": 0, "end_x": 100}
        )
        
        # Should be base or slightly above
        assert score <= 0.6


class TestCalculateRewardFromEpisode:
    """Test the episode reward calculator."""
    
    def test_basic_calculation(self):
        """Test basic reward calculation from episode data."""
        episode = {
            "steps": [
                {"action_type": "tap_element"},
                {"action_type": "type_text"},
                {"action_type": "press_enter"},
            ],
            "final_result": "PASS"
        }
        
        result = calculate_reward_from_episode(episode)
        
        assert result["step_count"] == 3
        assert result["step_penalty"] == pytest.approx(-0.15, abs=0.01)
        assert result["completion_bonus"] == 1.0
        assert result["final_result"] == "PASS"
    
    def test_failed_episode(self):
        """Test reward for failed episode."""
        episode = {
            "steps": [
                {"action_type": "tap_element"},
            ] * 10,
            "final_result": "FAIL"
        }
        
        result = calculate_reward_from_episode(episode)
        
        assert result["step_count"] == 10
        assert result["completion_bonus"] == 0.0
        assert result["total_reward"] < 0  # Should be negative due to penalties


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
