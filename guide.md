# NeMo Agent Toolkit - Event Planning System Setup Guide

This guide will help you migrate from CrewAI to NVIDIA NeMo Agent Toolkit for your event planning system.

## Prerequisites

- Python 3.11, 3.12, or 3.13
- NVIDIA NIM endpoint running on your VM with meta-llama3.1-8b-instruct
- SQLite3 (comes with Python)
- Git (for cloning NeMo Agent Toolkit repository)

## Installation Steps

### 1. Install NeMo Agent Toolkit

```bash
# Install from PyPI (recommended)
pip install nvidia-nat

# OR install from source for latest features
git clone https://github.com/NVIDIA/NeMo-Agent-Toolkit.git
cd NeMo-Agent-Toolkit
pip install -e .
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup SQLite Database

Run the database setup script to create your tables:

```bash
python database_setup.py
```

This will:
- Create `event_planning.db` with `moderators` and `participants` tables
- Optionally seed sample data for testing
- Display the database contents

**Database Schema:**

**Moderators Table:**
- `id` (Primary Key)
- `name` (Text, Required)
- `city` (Text)
- `description` (Text)
- `email` (Text)
- `phone` (Text)
- `expertise` (Text)
- `created_at` (Timestamp)

**Participants Table:**
- `id` (Primary Key)
- `name` (Text, Required)
- `email` (Text, Required, Unique)
- `company` (Text)
- `role` (Text)
- `phone` (Text)
- `created_at` (Timestamp)

### 4. Configure Your Environment

Update the configuration in `event_planning_nemo.py`:

```python
class Settings:
    def __init__(self):
        # NVIDIA NIM Configuration
        self.nim_base_url = "http://your-vm-ip:port/v1"  # Your NIM URL
        self.nim_api_key = "YOUR_API_KEY"  # Your API key
        self.model_name = "meta/llama-3.1-8b-instruct"
        
        # Database Configuration
        self.db_path = "event_planning.db"  # Path to your database
```

Or use environment variables (recommended):

```bash
export NIM_BASE_URL="http://your-vm-ip:port/v1"
export NVIDIA_API_KEY="your-api-key"
export DB_PATH="event_planning.db"
```

### 5. Update config.yml

```yaml
llms:
  event_llm:
    _type: nim
    api_key: "${NVIDIA_API_KEY}"
    base_url: "${NIM_BASE_URL}"
    model_name: "meta/llama-3.1-8b-instruct"
    temperature: 0.7
    max_tokens: 2048
```

## Usage

### Method 1: Direct Python Execution (Standalone)

The simplest method - runs without needing config.yml:

```python
from event_planning_nemo import EventPlanningWorkflow
import asyncio

# Initialize
planner = EventPlanningWorkflow()

# Generate themes
themes = planner.generate_event_themes("pickle ball event")
print(themes)

# Fetch moderators from database
moderators = asyncio.run(
    planner.fetch_moderators_async(moderator_names=["Jai Kumar"])
)

# Fetch participants from database
participants = asyncio.run(
    planner.fetch_participants_async(limit=10)
)

# Or fetch specific participants
participants = asyncio.run(
    planner.fetch_participants_async(
        participant_names=["Alice Smith", "Bob Johnson"]
    )
)

# Complete planning
event_details = {
    "start_date": "24-01-2025",
    "end_date": "24-01-2025",
    "start_time": "11:00 AM",
    "end_time": "5:00 PM",
    "location": "New York",
    "event_type": "Technical"
}

result = planner.start_event_planning(
    selected_theme=themes[0],
    event_details=event_details,
    moderators=moderators,
    participants=participants
)
```

### Method 2: Using Database Functions Directly

```python
from event_planning_nemo import db_manager

# Fetch all moderators
all_moderators = db_manager.fetch_moderators_from_db()

# Fetch specific moderators
specific_mods = db_manager.fetch_moderators_from_db(
    moderator_names=["Jai Kumar", "Priya Sharma"]
)

# Search moderators by expertise
tech_mods = db_manager.search_moderators_by_expertise("Technical")

# Fetch all participants with limit
participants = db_manager.fetch_participants_from_db(limit=50)

# Fetch specific participants
specific_parts = db_manager.fetch_participants_from_db(
    participant_names=["Alice Smith"]
)
```

### Method 2: Using NeMo CLI

```bash
# Run with config file
nat run --config_file config.yml --input "pickle ball event"

# Serve as API endpoint
nat serve --config_file config.yml

# Then call the API
curl --request POST \
  --url http://localhost:8000/generate \
  --header 'Content-Type: application/json' \
  --data '{"input_message": "Create a pickle ball event"}'
```

### Method 3: Using NeMo Runtime Loader

```python
import asyncio
from nat.runtime.loader import load_workflow

async def run_event_planning():
    async with load_workflow("config.yml") as workflow:
        async with workflow.run("pickle ball event") as runner:
            result = await runner.result(to_type=str)
            print(result)

asyncio.run(run_event_planning())
```

## Key Differences from CrewAI

### Architecture Comparison

| Feature | CrewAI | NeMo Agent Toolkit |
|---------|--------|-------------------|
| **Configuration** | Python classes | YAML + Python functions |
| **Agents** | Agent objects with roles | @function decorated Python functions |
| **Tasks** | Task objects | Function calls in workflow |
| **Orchestration** | Crew class | Workflow types (sequential, react_agent, router) |
| **LLM Config** | Per-agent | Centralized in YAML |

### Code Migration Map

**CrewAI:**
```python
theme_agent = Agent(
    role="Theme Generator",
    goal="Generate themes",
    llm=LLM(model="llama2")
)

task = Task(
    description="Generate themes",
    agent=theme_agent
)

crew = Crew(agents=[theme_agent], tasks=[task])
```

**NeMo:**
```python
@function(name="generate_themes")
async def generate_themes(event_idea: str) -> Dict:
    # Your logic here
    return {"themes": [...]}

# In config.yml:
functions:
  generate_themes:
    _type: generate_themes
    llm_name: event_llm
```

## Advanced Features

### 1. Add Profiling

```python
from nat.function_decorator import function

@function(name="generate_themes", profile=True)
async def generate_themes(event_idea: str):
    # Automatically tracks latency, tokens, costs
    pass
```

### 2. Add Observability

Add to config.yml:

```yaml
observability:
  phoenix:
    enabled: true
    endpoint: "http://localhost:6006"
```

### 3. Use Sequential Workflow

```yaml
workflow:
  _type: sequential
  steps:
    - function_name: generate_themes
      output_key: themes
    - function_name: select_theme
      input_key: themes
      output_key: selected
    - function_name: refine_plan
      input_key: selected
      output_key: final_plan
```

### 4. Use Router for Multi-Agent

```yaml
workflow:
  _type: router_agent
  branches: [theme_generator, plan_refiner, moderator_manager]
  llm_name: event_llm
```

## Troubleshooting

### Issue: "Module not found: nat"

```bash
# Make sure NeMo is installed
pip install nvidia-nat
```

### Issue: LLM connection fails

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Verify your base_url in config.yml matches
```

### Issue: Functions not registering

Make sure you're using the `@function` decorator:

```python
from nat.function_decorator import function

@function(name="my_function")  # Name is required!
async def my_function(param: str) -> Dict:
    pass
```

## Additional Resources

- [NeMo Agent Toolkit Documentation](https://docs.nvidia.com/nemo/agent-toolkit/latest/)
- [GitHub Repository](https://github.com/NVIDIA/NeMo-Agent-Toolkit)
- [Examples](https://github.com/NVIDIA/NeMo-Agent-Toolkit/tree/main/examples)
- [Migration Guide](https://docs.nvidia.com/nemo/agent-toolkit/latest/migration-guide.html)

## Questions?

If you have specific questions about your use case, feel free to ask!