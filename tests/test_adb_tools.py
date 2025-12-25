"""
Tests for the ADB Tools module.

Note: Some tests require an actual Android device/emulator connected.
Mark those with @pytest.mark.device
"""

import pytest
from unittest.mock import patch, MagicMock
import subprocess

from src.mobile_qa_agent.tools.adb_tools import (
    run_adb_command,
    get_screen_size,
    tap,
    type_text,
    press_enter,
    press_back,
    swipe,
    clear_field,
    clear_and_type,
    parse_ui_elements,
    find_element_by_text,
    check_device_connected
)


class TestRunAdbCommand:
    """Test the run_adb_command function."""
    
    @patch('subprocess.run')
    def test_basic_command(self, mock_run):
        """Test running a basic ADB command."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr=""
        )
        
        result = run_adb_command(["shell", "echo", "hello"])
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "adb"
        assert "shell" in call_args


class TestParseUiElements:
    """Test UI element parsing."""
    
    def test_parse_simple_xml(self):
        """Test parsing simple UI hierarchy XML."""
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <hierarchy>
            <node text="Button" class="android.widget.Button" 
                  clickable="true" bounds="[100,200][300,400]" />
            <node text="Label" class="android.widget.TextView" 
                  clickable="false" bounds="[100,500][300,600]" />
        </hierarchy>
        '''
        
        elements = parse_ui_elements(xml)
        
        assert len(elements) == 2
        
        # Check button
        button = elements[0]
        assert button['text'] == "Button"
        assert button['clickable'] == True
        assert button['center_x'] == 200  # (100 + 300) / 2
        assert button['center_y'] == 300  # (200 + 400) / 2
        
        # Check label
        label = elements[1]
        assert label['text'] == "Label"
        assert label['clickable'] == False
    
    def test_parse_empty_xml(self):
        """Test parsing empty XML."""
        xml = '<?xml version="1.0"?><hierarchy></hierarchy>'
        elements = parse_ui_elements(xml)
        assert elements == []
    
    def test_parse_with_content_desc(self):
        """Test parsing elements with content-desc."""
        xml = '''
        <hierarchy>
            <node content-desc="Menu button" class="android.widget.ImageButton"
                  clickable="true" bounds="[0,0][100,100]" />
        </hierarchy>
        '''
        
        elements = parse_ui_elements(xml)
        
        assert len(elements) == 1
        assert elements[0]['content_desc'] == "Menu button"


class TestFindElementByText:
    """Test element finding by text."""
    
    @patch('src.mobile_qa_agent.tools.adb_tools.get_ui_hierarchy')
    def test_find_exact_match(self, mock_hierarchy):
        """Test finding element with exact text match."""
        mock_hierarchy.return_value = '''
        <hierarchy>
            <node text="Create a vault" class="android.widget.Button"
                  clickable="true" bounds="[100,1000][900,1100]" />
            <node text="Use existing vault" class="android.widget.Button"
                  clickable="true" bounds="[100,1200][900,1300]" />
        </hierarchy>
        '''
        
        element = find_element_by_text("Create a vault")
        
        assert element is not None
        assert element['text'] == "Create a vault"
    
    @patch('src.mobile_qa_agent.tools.adb_tools.get_ui_hierarchy')
    def test_find_partial_match(self, mock_hierarchy):
        """Test finding element with partial text match."""
        mock_hierarchy.return_value = '''
        <hierarchy>
            <node text="Create a vault" class="android.widget.Button"
                  clickable="true" bounds="[100,1000][900,1100]" />
        </hierarchy>
        '''
        
        element = find_element_by_text("Create")
        
        assert element is not None
        assert "Create" in element['text']
    
    @patch('src.mobile_qa_agent.tools.adb_tools.get_ui_hierarchy')
    def test_not_found(self, mock_hierarchy):
        """Test when element is not found."""
        mock_hierarchy.return_value = '''
        <hierarchy>
            <node text="Other button" class="android.widget.Button"
                  clickable="true" bounds="[100,1000][900,1100]" />
        </hierarchy>
        '''
        
        element = find_element_by_text("Nonexistent button")
        
        assert element is None
    
    @patch('src.mobile_qa_agent.tools.adb_tools.get_ui_hierarchy')
    def test_prefer_clickable(self, mock_hierarchy):
        """Test that clickable elements are preferred."""
        mock_hierarchy.return_value = '''
        <hierarchy>
            <node text="Allow" class="android.widget.TextView"
                  clickable="false" bounds="[100,300][900,400]" />
            <node text="Allow" class="android.widget.Button"
                  clickable="true" bounds="[100,2000][900,2100]" />
        </hierarchy>
        '''
        
        element = find_element_by_text("Allow", prefer_clickable=True)
        
        assert element is not None
        assert element['clickable'] == True
        assert element['center_y'] > 1000  # Should find the button at bottom


class TestAdbActions:
    """Test ADB action functions."""
    
    @patch('src.mobile_qa_agent.tools.adb_tools.run_adb_command')
    def test_tap(self, mock_run):
        """Test tap function."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = tap(500, 1000)
        
        assert "Tapped" in result
        assert "500" in result
        assert "1000" in result
    
    @patch('src.mobile_qa_agent.tools.adb_tools.run_adb_command')
    def test_type_text(self, mock_run):
        """Test type_text function."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = type_text("Hello World")
        
        assert "Typed" in result
        mock_run.assert_called()
    
    @patch('src.mobile_qa_agent.tools.adb_tools.run_adb_command')
    def test_press_enter(self, mock_run):
        """Test press_enter function."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = press_enter()
        
        assert "enter" in result.lower()
    
    @patch('src.mobile_qa_agent.tools.adb_tools.run_adb_command')
    def test_press_back(self, mock_run):
        """Test press_back function."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = press_back()
        
        assert "back" in result.lower()
    
    @patch('src.mobile_qa_agent.tools.adb_tools.run_adb_command')
    def test_swipe(self, mock_run):
        """Test swipe function."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = swipe(100, 500, 100, 1500)
        
        assert "Swiped" in result


class TestDeviceConnection:
    """Test device connection checking."""
    
    @patch('src.mobile_qa_agent.tools.adb_tools.run_adb_command')
    def test_device_connected(self, mock_run):
        """Test when device is connected."""
        mock_run.return_value = MagicMock(
            stdout="List of devices attached\nemulator-5554\tdevice\n"
        )
        
        assert check_device_connected() == True
    
    @patch('src.mobile_qa_agent.tools.adb_tools.run_adb_command')
    def test_no_device(self, mock_run):
        """Test when no device is connected."""
        mock_run.return_value = MagicMock(
            stdout="List of devices attached\n"
        )
        
        assert check_device_connected() == False


# Mark tests that require actual device
@pytest.mark.device
class TestWithDevice:
    """Tests that require actual device connection."""
    
    def test_take_screenshot(self):
        """Test taking a screenshot."""
        from src.mobile_qa_agent.tools.adb_tools import take_screenshot
        
        result = take_screenshot()
        
        # Should be base64 string or error
        assert len(result) > 100 or result.startswith("Error")
    
    def test_get_screen_size(self):
        """Test getting screen size."""
        width, height = get_screen_size()
        
        assert width > 0
        assert height > 0
        assert width < height  # Portrait mode


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not device"])
