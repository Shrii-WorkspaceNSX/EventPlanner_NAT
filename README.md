# Event Planning System - NVIDIA NeMo Agent Toolkit

A complete event planning system using NVIDIA NeMo Agent Toolkit with:
- 🤖 AI-powered theme generation using meta-llama3.1-8b-instruct
- 📋 Automated event plan refinement
- 👥 SQLite database integration for moderators and participants
- 🚀 Full NeMo Agent Toolkit integration with proper function registration

## 🏗️ Project Structure

```
event-planning-project/
├── event_planning_nemo/         # Main package directory
│   ├── __init__.py             # Package initialization
│   ├── register.py             # Function registration
│   └── event_planning_nemo.py  # Main implementation
├── pyproject.toml              # Package configuration (CRITICAL!)
├── config.yml                  # NeMo configuration
├── database_setup.py           # Database setup script
├── setup.sh                    # Automated setup script
├── .env                        # Environment variables
├── event_planning.db           # SQLite database
└── README.md                   # This file
```

## ⚡ Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# 1. Create project directory and add all files
mkdir event-planning-project
cd event-planning-project

# 2. Create the package directory
mkdir event_planning_nemo

# 3. Add all Python files to event_planning_nemo/
#    - __init__.py
#    - register.py
#    - event_planning_nemo.py

# 4. Add to root directory:
#    - pyproject.toml
#    - config.yml
#    - database_setup.py
#    - .env.template
#    - setup.sh

# 5. Make setup script executable and run
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install package in editable mode (REQUIRED for nat CLI)
pip install -e .

# 3. Install dependencies
pip install litellm pydantic python-dotenv

# 4. Configure environment
cp .env.template .env
nano .env  # Edit with your NIM URL and API key

# 5. Setup database
python database_setup.py

# 6. Verify registration
nat info components | grep event
```

## 🔑 Critical Configuration

### 1. pyproject.toml Entry Point

This is **REQUIRED** for NeMo to find your functions:

```toml
[project.entry-points."nat.components"]
event_planning = "event_planning_nemo.register"
```

### 2. Environment Variables (.env)

```env
NIM_BASE_URL=http://your-vm-ip:port/v1
NVIDIA_API_KEY=your-api-key
MODEL_NAME=meta/llama3.1-8b-instruct
DB_PATH=event_planning.db
```

### 3. Function Registration Pattern

Functions MUST use the `yield FunctionInfo` pattern:

```python
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig
from pydantic import BaseModel, Field

# Input/Output schemas
class MyInput(BaseModel):
    param: str = Field(description="Parameter description")

class MyOutput(BaseModel):
    result: str = Field(description="Result description")

# Config class
class MyFunctionConfig(FunctionBaseConfig, name="my_function"):
    pass

# Registered function
@register_function(config_type=MyFunctionConfig)
async def my_function(config: MyFunctionConfig, builder: Builder):
    async def _inner(input_data: MyInput) -> MyOutput:
        # Your logic here
        return MyOutput(result="...")
    
    # CRITICAL: Must yield FunctionInfo
    yield FunctionInfo.from_fn(_inner, description="What this does")
```

**Key Points:**
- Must use `async def` with `yield`
- Inner function does the actual work
- Outer function yields `FunctionInfo`
- Input/Output must be Pydantic models
- Config class must have `name=` parameter

## 📊 Database Schema

The system uses SQLite3 with two tables:

### Moderators Table
```sql
CREATE TABLE moderators (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    description TEXT,
    email TEXT,
    phone TEXT,
    expertise TEXT,
    created_at TIMESTAMP
);
```

### Participants Table
```sql
CREATE TABLE participants (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    company TEXT,
    role TEXT,
    phone TEXT,
    created_at TIMESTAMP
);
```

## 🎯 Usage

### Method 1: NeMo CLI (Recommended)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run with CLI
nat run --config_file config.yml --input "Create a pickle ball event"

# Check registered functions
nat info components | grep -E "generate_event_themes|refine_event_plan"
```

### Method 2: Direct Python Usage

```python
from event_planning_nemo import EventPlanningWorkflow, db_manager

# Initialize workflow
planner = EventPlanningWorkflow()

# Generate themes
themes = planner.generate_event_themes("technical conference")
print(f"Generated {len(themes)} themes")

# Fetch data from database
moderators = db_manager.fetch_moderators_from_db()
participants = db_manager.fetch_participants_from_db(limit=50)

# Create event plan
event_details = {
    "start_date": "15-02-2025",
    "end_date": "16-02-2025",
    "start_time": "9:00 AM",
    "end_time": "5:00 PM",
    "location": "Convention Center",
    "event_type": "Technical Conference"
}

plan = planner.start_event_planning(
    selected_theme=themes[0],
    event_details=event_details,
    moderators=moderators,
    participants=participants
)
```

### Method 3: Import as Package

```python
import asyncio
from event_planning_nemo.register import (
    generate_event_themes,
    GenerateEventThemesConfig
)

async def main():
    config = GenerateEventThemesConfig(event_idea="sports event")
    result = await generate_event_themes(config, None)
    print(result['themes'])

asyncio.run(main())
```

## 🐛 Troubleshooting

### Error: "Requested functions type not found"

**Cause**: NeMo can't find your registered functions.

**Solutions**:
```bash
# 1. Check if package is installed
pip list | grep event-planning-nemo

# 2. Verify entry point
cat pyproject.toml | grep -A 2 "entry-points"

# 3. Reinstall in editable mode
pip uninstall event-planning-nemo -y
pip install -e .

# 4. Check function registration
nat info components | grep event
```

### Error: "Module not found: event_planning_nemo"

**Cause**: Package structure is incorrect or not installed.

**Solution**:
```bash
# Check directory structure
ls -la event_planning_nemo/
# Should show: __init__.py, register.py, event_planning_nemo.py

# Reinstall
pip install -e .
```

### Functions not showing in `nat info components`

```bash
# Force clean reinstall
pip uninstall event-planning-nemo -y
rm -rf build/ dist/ *.egg-info event_planning_nemo.egg-info
pip install -e .

# Restart terminal/shell
# Then check again
nat info components
```

### Database connection errors

```bash
# Check database exists
ls -la event_planning.db

# Recreate if needed
rm event_planning.db
python database_setup.py
```

## 📚 Function Reference

### 1. generate_event_themes
Generates 5 creative event themes based on an idea.

**Config Parameters**:
- `event_idea` (str): Base idea for the event
- `llm_name` (str): LLM to use (default: "event_llm")

**Returns**: Dict with `themes` list and `raw_response`

### 2. refine_event_plan
Creates detailed event plan with agenda and invitation.

**Config Parameters**:
- `selected_theme` (str): Chosen theme
- `start_date`, `end_date` (str): Event dates
- `start_time`, `end_time` (str): Event times
- `location` (str): Event location
- `event_type` (str): Type of event
- `moderators` (list): List of moderator dicts
- `llm_name` (str): LLM to use

**Returns**: Dict with `refined_plan` and `event_details`

### 3. fetch_moderators
Fetches moderators from SQLite database.

**Config Parameters**:
- `moderator_names` (list, optional): Specific names to fetch
- `expertise` (str, optional): Search by expertise

**Returns**: Dict with `moderators` list and `count`

### 4. fetch_participants
Fetches participants from SQLite database.

**Config Parameters**:
- `participant_names` (list, optional): Specific names to fetch
- `limit` (int, optional): Maximum number to fetch

**Returns**: Dict with `participants` list and `count`

## 🔄 Migration from CrewAI

| CrewAI Component | NeMo Equivalent |
|------------------|-----------------|
| `Agent` class | `@register_function` decorated function |
| `Task` class | Function call in workflow |
| `Crew` class | `workflow` in config.yml |
| `LLM(model=...)` per agent | Centralized `llms` in config.yml |
| Python-based config | YAML-based config.yml |

## ✅ Verification Checklist

After setup, verify:

- [ ] Package is installed: `pip list | grep event-planning-nemo`
- [ ] Functions are registered: `nat info components | grep event`
- [ ] Database exists: `ls event_planning.db`
- [ ] Environment configured: `cat .env`
- [ ] CLI works: `nat run --config_file config.yml --input "test"`
- [ ] Direct import works: `python -c "from event_planning_nemo import EventPlanningWorkflow"`

## 📖 Additional Resources

- [NeMo Agent Toolkit Docs](https://docs.nvidia.com/nemo/agent-toolkit/)
- [Function Registration Guide](https://docs.nvidia.com/nemo/agent-toolkit/latest/extend/functions.html)
- [Plugin System](https://docs.nvidia.com/nemo/agent-toolkit/latest/extend/sharing-components.html)
- [NVIDIA NIM Documentation](https://docs.nvidia.com/nim/)

## 🤝 Support

For issues:
1. Check the troubleshooting section above
2. Verify all files are in correct locations
3. Ensure package is installed with `pip install -e .`
4. Check NeMo Agent Toolkit GitHub issues

## 📝 License

This project uses NVIDIA NeMo Agent Toolkit. See their license for details.