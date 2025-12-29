# 🧪 Test Cases Reference

## Overview

The Mobile QA Agent includes 10 pre-built test cases for the Obsidian mobile app. Each test is designed to validate specific functionality and demonstrate the agent's capabilities.

---

## Test Summary

| # | Name | Reset | Expected | Description |
|---|------|-------|----------|-------------|
| 1 | Create Vault | ✅ | PASS | Create a new vault from scratch |
| 2 | Create Note | ❌ | PASS | Create a note with title and body |
| 3 | Verify Appearance Icon | ❌ | FAIL | Check if icon is red (it's not) |
| 4 | Find Print to PDF | ❌ | FAIL | Search for non-existent feature |
| 5 | Create Multiple Notes | ❌ | PASS | Create two notes sequentially |
| 6 | Search Notes | ❌ | PASS | Use search to find a note |
| 7 | Delete Note | ❌ | PASS | Delete an existing note |
| 8 | Change Theme | ❌ | PASS | Switch to dark theme |
| 9 | Create Vault + Folder | ✅ | PASS | Create vault in a new folder |
| 10 | Link Notes | ❌ | PASS | Create link between two notes |

**Reset Column**: Whether app data is cleared before the test

---

## Detailed Test Cases

### Test 1: Create Vault

**Purpose**: Verify that a new vault can be created from the initial app state.

**Starting State**: Fresh app install (reset required)

**Steps**:
1. Tap "Create a vault"
2. Tap "Continue without sync"
3. Enter vault name "InternVault"
4. Tap "Create a vault" button
5. Select folder (USE THIS FOLDER)
6. Grant permissions if prompted
7. Verify vault is entered

**Success Condition**: Screen shows "Create new note" option (inside vault)

**Prompt Used**: `VAULT_CREATION_PROMPT`

---

### Test 2: Create Note

**Purpose**: Verify that a note can be created with title and content.

**Starting State**: Inside an existing vault

**Steps**:
1. Tap "Create new note"
2. Enter title "Meeting Notes"
3. Enter body "Daily Standup"
4. Verify note is saved

**Success Condition**: Note exists with title "Meeting Notes"

**Prompt Used**: `NOTE_CREATION_PROMPT`

---

### Test 3: Verify Appearance Icon Color

**Purpose**: Check if the Appearance settings icon is red colored. This is an intentional FAIL test - the icon is actually purple/default, not red.

**Starting State**: Inside vault with a note open

**Steps**:
1. Tap expand/sidebar button (100, 128)
2. Tap settings gear icon (280, 75)
3. Find "Appearance" option
4. Check icon color

**Success Condition**: Appearance icon is red (it's not, so test should FAIL)

**Prompt Used**: `SETTINGS_NAVIGATION_PROMPT`

**Note**: This test demonstrates the agent's ability to correctly identify when something is NOT as expected.

---

### Test 4: Find Print to PDF

**Purpose**: Search for a "Print to PDF" feature that doesn't exist. This is an intentional FAIL test.

**Starting State**: Inside vault

**Steps**:
1. Open menu (three dots)
2. Search through menu options
3. Look for "Print to PDF"

**Success Condition**: Print to PDF option exists (it doesn't, so test should FAIL)

**Prompt Used**: `GENERIC_TEST_PROMPT`

**Note**: This test demonstrates the agent's ability to correctly identify missing features.

---

### Test 5: Create Multiple Notes

**Purpose**: Verify that multiple notes can be created in sequence without editing existing notes.

**Starting State**: Inside vault, viewing an existing note

**Steps**:
1. Tap + icon (600, 2292)
2. Tap "Create new note"
3. Enter title "Project Ideas"
4. Enter body content
5. Tap title area (540, 129) to restore bottom bar
6. Repeat steps 1-5 for second note "Todo List"

**Success Condition**: Both notes "Project Ideas" and "Todo List" exist

**Prompt Used**: `MULTI_NOTE_CREATION_PROMPT`

**Key Challenge**: After typing in the body, the bottom bar changes and the + icon disappears. Agent must tap the title area to restore the correct bottom bar before creating the next note.

---

### Test 6: Search Notes

**Purpose**: Verify the search functionality works.

**Starting State**: Inside vault with existing notes

**Steps**:
1. Tap search icon (148, 2292)
2. See search screen with "Find or create a note..."
3. Type a note name from the visible list
4. Verify search results appear

**Success Condition**: Search results show matching notes

**Prompt Used**: `SEARCH_NOTE_PROMPT`

---

### Test 7: Delete Note

**Purpose**: Verify that a note can be deleted.

**Starting State**: Inside vault, viewing a note

**Steps**:
1. Tap three dots menu (990, 128)
2. Scroll down in menu
3. Tap "Delete file" (red text at bottom)
4. Confirm deletion if prompted

**Success Condition**: Note is deleted from vault

**Prompt Used**: `DELETE_NOTE_PROMPT`

---

### Test 8: Change Theme

**Purpose**: Verify that the app theme can be changed to dark mode.

**Starting State**: Inside vault

**Steps**:
1. Tap expand/sidebar button (100, 128)
2. Tap settings gear icon (280, 75)
3. Tap "Appearance"
4. Tap "Proper Dark" theme option
5. Tap back arrow (100, 128) to exit

**Success Condition**: App theme is changed to dark mode

**Prompt Used**: `CHANGE_THEME_PROMPT`

---

### Test 9: Create Vault with New Folder

**Purpose**: Create a vault and store it in a newly created folder (not an existing one).

**Starting State**: Fresh app install (reset required)

**Steps**:
1. Tap "Create a vault"
2. Tap "Continue without sync"
3. Enter vault name "TestVault"
4. Tap "Create a vault" button
5. **Tap new folder icon (253, 128)** - NOT "Use this folder"
6. Enter folder name "TestVault"
7. Tap "OK"
8. Tap "USE THIS FOLDER"
9. Grant permissions if prompted

**Success Condition**: New folder created and vault setup initiated

**Prompt Used**: `CREATE_VAULT_NEW_FOLDER_PROMPT`

**Key Difference from Test 1**: Instead of selecting an existing folder, this test creates a new folder first.

---

### Test 10: Link Notes

**Purpose**: Create a link from one note to another using Obsidian's `[[]]` syntax.

**Starting State**: Inside vault, viewing a note (e.g., "Project Ideas")

**Steps**:
1. Remember current note's title
2. Tap in body area (title_y + 100)
3. Type `[[` to start link syntax
4. Select a DIFFERENT note from suggestions (e.g., "Meeting Notes")
5. Verify link appears in body

**Success Condition**: Note contains a link to a different note (title ≠ linked note)

**Prompt Used**: `LINK_NOTES_PROMPT`

---

## Test Dependencies

Some tests depend on the results of previous tests:

```
Test 1 (Create Vault)
    │
    ├──▶ Test 2 (Create Note) ──▶ Test 3, 4, 5, 6, 7, 8, 10
    │
    └──▶ Test 9 (Create Vault + Folder) - Independent, requires reset
```

**Recommended Run Order**:
- For full test suite: Run tests 1-8, then reset for test 9, then test 10
- For individual testing: Test 1 or 9 first (with reset), then any others

---

## Expected Results Matrix

| Test | Expected | Why |
|------|----------|-----|
| 1 | PASS | Vault creation is core functionality |
| 2 | PASS | Note creation is core functionality |
| 3 | FAIL | Icon is purple, not red (intentional) |
| 4 | FAIL | Feature doesn't exist (intentional) |
| 5 | PASS | Multi-note creation works |
| 6 | PASS | Search functionality works |
| 7 | PASS | Delete functionality works |
| 8 | PASS | Theme switching works |
| 9 | PASS | Folder creation works |
| 10 | PASS | Note linking works |

**Pass Rate**: 8/10 (80%) expected
- 2 tests are designed to FAIL to validate negative testing capability

---

## Adding Custom Tests

To add a new test case, update `TEST_CASES` in `main.py`:

```python
TEST_CASES = {
    # ... existing tests ...
    
    11: {
        "name": "My Custom Test",
        "description": "Description of what to test",
        "expected_result": "PASS",  # or "FAIL"
        "app_package": "md.obsidian",
        "reset_app": False,  # True if fresh start needed
        "success_condition": "What defines success",
        "ground_truth_steps": [
            "step 1",
            "step 2",
            # ...
        ]
    }
}
```

Then add a corresponding prompt in `agent.py` and update `get_test_prompt()` to select it.