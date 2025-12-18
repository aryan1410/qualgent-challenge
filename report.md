# Framework Decision Memo: Mobile QA Multi-Agent System

## Decision Summary
**Selected Framework: Google Agent Development Kit (ADK)**

## Context
For building a Supervisor-Planner-Executor multi-agent system for mobile QA automation on Android, I evaluated two frameworks:
- **Simular's Agent S3**: State-of-the-art computer-use agent framework (69.9% on OSWorld, 71.6% on AndroidWorld)
- **Google's Agent Development Kit (ADK)**: Flexible multi-agent orchestration framework

## Why Google ADK?

### 1. Native Multi-Agent Architecture
ADK is **designed from the ground up** for multi-agent systems with built-in patterns for:
- **Hierarchical agent structures** (perfect for Supervisor → Planner → Executor)
- **SequentialAgent, ParallelAgent, LoopAgent** workflow patterns
- **Agent delegation and transfer** mechanisms

Agent S3 is optimized for a single autonomous agent that combines planning and execution. Retrofitting it into a Supervisor-Planner-Executor hierarchy would require significant custom work.

### 2. Free Groq Integration
ADK integrates seamlessly with **Groq models (free tier available)**, which the assignment recommends. Agent S3 is optimized for GPT-5 and Claude, with Groq being secondary.

### 3. Simpler Custom Tool Integration
For this task, I need to wrap ADB commands as tools. ADK makes this trivial:
```python
@tool
def tap_screen(x: int, y: int) -> str:
    """Tap at screen coordinates"""
    subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])
    return f"Tapped at ({x}, {y})"
```

### 4. Cleaner Role Separation
The assignment requires **distinct roles** (Planner, Executor, Supervisor). ADK's `LlmAgent` with custom instructions makes each agent's responsibility explicit and swappable. Agent S3's monolithic architecture blends these concerns.

### 5. Model Swappability
ADK is **model-agnostic** with LiteLLM integration supporting OpenAI, Anthropic, Groq, and more. This directly addresses the evaluation criterion: "Can we swap the LLM model easily?"

## Trade-offs Acknowledged
- **Agent S3 has superior AndroidWorld benchmarks** (71.6% vs. ADK's general-purpose approach)
- **Agent S3's grounding models** (UI-TARS) are state-of-the-art for element detection
- For **production mobile QA**, Agent S3 would likely perform better

However, for this **learning-focused intern challenge**, ADK's explicit multi-agent patterns, free Groq access, and cleaner code structure make it the better pedagogical choice.

## Conclusion
Google ADK provides the cleanest path to implementing the required Supervisor-Planner-Executor architecture with minimal boilerplate, free model access, and clear code organization that demonstrates understanding of multi-agent design patterns.