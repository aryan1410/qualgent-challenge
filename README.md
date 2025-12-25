# Mobile QA Agent - Automated Android Testing with Google ADK

A multi-agent mobile QA testing framework built with **Google Agent Development Kit (ADK)**. This system uses AI vision models to analyze Android app screenshots and execute automated test cases through ADB (Android Debug Bridge).

## Features

- **🤖 Multi-Agent Architecture**: Built on Google ADK with specialized agents for planning, execution, and evaluation
- **📊 Comprehensive Metrics System**: 
  - Step-by-step reward calculation
  - Subgoal tracking and completion rates
  - Ground truth plan comparison
  - Action relevance scoring
- **🎯 10 Pre-defined Test Cases**: Ready-to-run tests for Obsidian app
- **📱 ADB Integration**: Direct Android device control via UI Automator
- **📈 Reward Function**:
  - **-0.05 per step**: Efficiency penalty
  - **+0.2 per subgoal**: Progress reward
  - **+1.0 completion**: Success bonus
- **🔍 Visual UI Analysis**: Screen state detection and element parsing
- **📁 Results Tracking**: JSON-based episode recording with detailed metrics

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mobile QA Orchestrator                        │
│                  (Google ADK Root Agent)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ PlannerAgent  │ │ ExecutorAgent │ │SupervisorAgent│
├───────────────┤ ├───────────────┤ ├───────────────┤
│ • Gemini 2.0  │ │ • ADB Tools   │ │ • Gemini 2.0  │
│ • UI Analysis │ │ • UI Automator│ │ • Evaluation  │
│ • Decision    │ │ • Screenshots │ │ • Bug Reports │
└───────────────┘ └───────────────┘ └───────────────┘
```

## Installation

### Prerequisites

1. **Python 3.10+**
2. **Android SDK with ADB**
   - Download from [Android Studio](https://developer.android.com/studio)
   - Ensure `adb` is in your PATH
3. **Android Emulator or Device**
   - API Level 30+ recommended
   - Obsidian app installed (`md.obsidian`)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/aryan/mobile-qa-agent.git
cd mobile-qa-agent

# Run setup script
chmod +x setup.sh
./setup.sh
```

### Manual Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .

# Configure API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### API Key Setup

Get a Google API key from [Google AI Studio](https://aistudio.google.com/apikey):

```bash
# Option 1: Google AI Studio (Recommended for development)
export GOOGLE_API_KEY="your-api-key-here"

# Option 2: Vertex AI (For production)
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
```

## Usage

### List Available Tests

```bash
python -m src.main --list
```

### Run a Single Test

```bash
# Run test 1 (Create Vault)
python -m src.main --task 1

# Run with reward metrics
python -m src.main --task 1 --calculate-reward
```

### Run All Tests

```bash
python -m src.main --task all
```

### Using ADK Web Interface

```bash
# Navigate to src directory
cd src

# Start ADK web UI
adk web
```

Then open http://localhost:8000 in your browser.

### Interactive Mode

```bash
python -m src.main
# Follow the interactive menu
```

## Test Cases

| # | Name | Description | Expected |
|---|------|-------------|----------|
| 1 | Create Vault | Create vault named 'InternVault' | PASS |
| 2 | Create Note | Create note with title and content | PASS |
| 3 | Verify Icon Color | Check Appearance icon is Red | FAIL* |
| 4 | Find Print to PDF | Search for print option | FAIL* |
| 5 | Create Multiple Notes | Create two notes | PASS |
| 6 | Search Notes | Use search function | PASS |
| 7 | Delete Note | Delete an existing note | PASS |
| 8 | Change Theme | Switch to dark mode | PASS |
| 9 | Create Folder | Create folder in vault | PASS |
| 10 | Link Notes | Create link between notes | PASS |

*Tests 3-4 are intentionally designed to fail to demonstrate bug detection capabilities.

## Metrics System

### Reward Function

The framework uses a comprehensive reward system for agent evaluation:

```
Total Reward = Step Penalty + Subgoal Reward + Completion Bonus

Where:
- Step Penalty = -0.05 × number_of_steps
- Subgoal Reward = +0.2 × subgoals_achieved
- Completion Bonus = +1.0 if PASS, 0 otherwise
```

### Example Output

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
   Subgoal Reward: 1.20
   Completion Bonus: 1.00
   TOTAL REWARD: 1.80

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

### Metrics Tracked

- **Step-level metrics**: Action type, duration, success, relevance score
- **Subgoal tracking**: Automatic detection of intermediate achievements
- **Ground truth comparison**: How well agent follows expected plan
- **Reward calculation**: Per-step and cumulative rewards
- **Timing analysis**: Duration and efficiency metrics

## Project Structure

```
mobile-qa-agent/
├── src/
│   ├── main.py                 # Main runner and CLI
│   └── mobile_qa_agent/
│       ├── __init__.py
│       ├── agent.py            # ADK agent definitions
│       └── tools/
│           ├── __init__.py
│           ├── adb_tools.py    # ADB and UI Automator functions
│           └── metrics.py      # Metrics tracking system
├── tests/
│   ├── test_adb_tools.py
│   ├── test_metrics.py
│   └── test_agent.py
├── results/                    # Test results (JSON)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── METRICS.md
│   └── CONTRIBUTING.md
├── prompts/                    # Agent prompt templates
├── setup.sh                    # Setup script
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_metrics.py -v

# Run with coverage
python -m pytest --cov=src tests/
```

### Code Style

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/
```

## Troubleshooting

### Common Issues

1. **ADB not found**
   ```bash
   # Add Android SDK to PATH
   export PATH=$PATH:$ANDROID_HOME/platform-tools
   ```

2. **No device connected**
   ```bash
   # Check connected devices
   adb devices
   
   # Start emulator
   emulator -avd YourAVDName
   ```

3. **API key errors**
   ```bash
   # Verify API key is set
   echo $GOOGLE_API_KEY
   
   # Test API connection
   python -c "import google.generativeai as genai; print('OK')"
   ```

4. **Obsidian not installed**
   ```bash
   # Install via ADB
   adb install obsidian.apk
   
   # Or install from Play Store on emulator
   ```

### Debug Mode

```bash
# Enable verbose logging
python -m src.main --task 1 --verbose

# Check ADB connection
adb shell echo "Connected"

# Get UI hierarchy manually
adb shell uiautomator dump /sdcard/ui.xml
adb shell cat /sdcard/ui.xml
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## Citation

```bibtex
@misc{mobile_qa_agent_adk,
  title={Mobile QA Agent: Multi-Agent Testing Framework with Google ADK},
  author={Aryan},
  year={2024},
  url={https://github.com/aryan/mobile-qa-agent},
  note={Built with Google Agent Development Kit for automated Android testing}
}
```

## Acknowledgments

- [Google Agent Development Kit (ADK)](https://github.com/google/adk-python)
- [Android Debug Bridge (ADB)](https://developer.android.com/tools/adb)
- [UI Automator](https://developer.android.com/training/testing/ui-automator)
- [Obsidian](https://obsidian.md/) for testing target

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/aryan/mobile-qa-agent/issues)
- 💬 [Discussions](https://github.com/aryan/mobile-qa-agent/discussions)
