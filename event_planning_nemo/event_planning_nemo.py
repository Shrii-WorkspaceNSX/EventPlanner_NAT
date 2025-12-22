"""
Event Planning System using NVIDIA NeMo Agent Toolkit
This module provides custom functions for event planning with SQLite database integration
"""

import re
import asyncio
import sqlite3
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from litellm import completion

from nat.data_models.function import FunctionBaseConfig
from nat.cli.register_workflow import register_function
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo

# Load environment variables
load_dotenv()


# Configuration settings
class Settings:
    def __init__(self):
        # NVIDIA NIM Configuration
        self.nim_base_url = os.getenv("NIM_BASE_URL", "http://localhost:8202")
        self.nim_api_key = os.getenv("NVIDIA_API_KEY", "")
        self.model_name = os.getenv("MODEL_NAME", "meta/llama3.1-8b-instruct")
        
        # Database Configuration
        self.db_path = os.getenv("DB_PATH", "event_planning.db")


settings = Settings()


# ==================== Database Helper Functions ====================

class DatabaseManager:
    """Manage SQLite3 database operations for moderators and participants."""
    
    def __init__(self, db_path: str = ""):
        self.db_path = db_path or settings.db_path
    
    def get_connection(self):
        """Create and return a database connection."""
        return sqlite3.connect(self.db_path)
    
    def fetch_moderators_from_db(
        self, 
        moderator_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch moderators from the database."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if moderator_names:
                placeholders = ','.join('?' * len(moderator_names))
                query = f"""
                    SELECT name, city, description, email, phone, expertise
                    FROM moderators 
                    WHERE name IN ({placeholders})
                """
                cursor.execute(query, moderator_names)
            else:
                query = """
                    SELECT name, city, description, email, phone, expertise
                    FROM moderators
                """
                cursor.execute(query)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        
        except sqlite3.Error as e:
            print(f"Database error fetching moderators: {e}")
            return []
        
        finally:
            conn.close()
    
    def fetch_participants_from_db(
        self,
        participant_names: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch participants from the database."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if participant_names:
                placeholders = ','.join('?' * len(participant_names))
                query = f"""
                    SELECT name, email, company, role, phone
                    FROM participants 
                    WHERE name IN ({placeholders})
                """
                params = participant_names
            else:
                query = """
                    SELECT name, email, company, role, phone
                    FROM participants
                """
                params = []
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        
        except sqlite3.Error as e:
            print(f"Database error fetching participants: {e}")
            return []
        
        finally:
            conn.close()


# Global database manager instance
db_manager = DatabaseManager()


# ==================== Input/Output Schema Classes ====================

class EventIdeaInput(BaseModel):
    """Input schema for theme generation."""
    event_idea: str = Field(description="The base idea or concept for the event")


class ThemesOutput(BaseModel):
    """Output schema for generated themes."""
    themes: List[str] = Field(description="List of generated event themes")


class EventPlanInput(BaseModel):
    """Input schema for event plan refinement."""
    selected_theme: str = Field(description="The chosen event theme")
    start_date: str = Field(description="Event start date")
    end_date: str = Field(description="Event end date")
    start_time: str = Field(description="Event start time")
    end_time: str = Field(description="Event end time")
    location: str = Field(description="Event location")
    event_type: str = Field(description="Type of event")
    moderators: List[Dict[str, str]] = Field(default_factory=list, description="List of moderators")


class EventPlanOutput(BaseModel):
    """Output schema for refined event plan."""
    refined_plan: str = Field(description="Detailed event plan with agenda and invitation")


class ModeratorsInput(BaseModel):
    """Input schema for fetching moderators."""
    moderator_names: Optional[List[str]] = Field(default=None, description="Optional list of moderator names")


class ModeratorsOutput(BaseModel):
    """Output schema for moderators."""
    moderators: List[Dict[str, Any]] = Field(description="List of moderator information")


class ParticipantsInput(BaseModel):
    """Input schema for fetching participants."""
    participant_names: Optional[List[str]] = Field(default=None, description="Optional list of participant names")
    limit: Optional[int] = Field(default=None, description="Optional limit on results")


class ParticipantsOutput(BaseModel):
    """Output schema for participants."""
    participants: List[Dict[str, Any]] = Field(description="List of participant information")

class HumanPromptTextInput(BaseModel):
    prompt: str


# ==================== Function Configuration Classes ====================


class GenerateEventThemesConfig(FunctionBaseConfig, name="generate_event_themes"):
    """Configuration for event theme generation function."""
    pass


class RefineEventPlanConfig(FunctionBaseConfig, name="refine_event_plan"):
    """Configuration for event plan refinement function."""
    pass


class FetchModeratorsConfig(FunctionBaseConfig, name="fetch_moderators"):
    """Configuration for moderator fetching function."""
    pass


class FetchParticipantsConfig(FunctionBaseConfig, name="fetch_participants"):
    """Configuration for participant fetching function."""
    pass


# ==================== Registered Functions with FunctionInfo Pattern ====================

@register_function(config_type=GenerateEventThemesConfig)
async def generate_event_themes(
    config: GenerateEventThemesConfig,
    builder: Builder
):
    """
    Generate five professional, creative, and distinct event themes.
    
    This function uses the FunctionInfo pattern required by NeMo Agent Toolkit.
    """
    
    async def _generate_themes(input_data: EventIdeaInput) -> ThemesOutput:
        """Inner function that does the actual theme generation."""
        prompt = (
            f"Generate exactly five professional, creative, and distinct event ideas "
            f"with titles and detailed descriptions based on: '{input_data.event_idea}'. "
            f"Format each theme as a numbered bold title followed by its description"
        )
        
        try:
            response = completion(
                model=settings.model_name,
                messages=[{"content": prompt, "role": "user"}],
                api_base=settings.nim_base_url,
                api_key=settings.nim_api_key
            )
            
            # Safe extraction with proper None checks
            if response is None:
                raise ValueError("LLM returned None response")
            
            choices = response["choices"] if isinstance(response, dict) else None
            if not choices or len(choices) == 0:
                raise ValueError("LLM response has no choices")
            
            message = choices[0].get("message")
            if not message:
                raise ValueError("LLM response has no message")
            
            content = message.get("content")
            if not content:
                raise ValueError("LLM response has no content")
            
            raw_response = content.strip()
            
            # Split themes by numbered format
            themes = re.split(r"\*\*\d+\.\s*", raw_response)
            if themes and not themes[0].strip():
                themes.pop(0)
            cleaned_themes = [theme.replace("\n\n", "\n").strip() for theme in themes if theme]
            
            if not cleaned_themes:
                raise ValueError("Failed to extract themes from LLM response")
            
            return ThemesOutput(themes=cleaned_themes)
            
        except Exception as e:
            print(f"Error generating themes: {e}")
            # Return default themes as fallback
            return ThemesOutput(themes=[
                "**Event Theme 1**: Unable to generate themes. Please check your LLM configuration.",
                "**Event Theme 2**: Error: " + str(e),
                "**Event Theme 3**: Verify NIM_BASE_URL and NVIDIA_API_KEY are set correctly.",
                "**Event Theme 4**: Ensure your NVIDIA NIM endpoint is running.",
                "**Event Theme 5**: Check network connectivity to the NIM server."
            ])
    
    # Yield FunctionInfo to register the function with NeMo Agent Toolkit
    yield FunctionInfo.from_fn(
        _generate_themes,
        description="Generate five creative and professional event themes based on an event idea"
    )


@register_function(config_type=RefineEventPlanConfig)
async def refine_event_plan(
    config: RefineEventPlanConfig,
    builder: Builder
):
    """
    Refine a selected theme into a detailed event plan.
    
    This function uses the FunctionInfo pattern required by NeMo Agent Toolkit.
    """
    
    async def _refine_plan(input_data: EventPlanInput) -> EventPlanOutput:
        """Inner function that does the actual plan refinement."""
        # Format moderator information
        moderator_descriptions = " ".join([
            f"{moderator['name']} from {moderator['city']} with expertise in {moderator.get('description', 'events')}"
            for moderator in input_data.moderators
        ])
        moderators_str = f"The moderators for this event are: {moderator_descriptions}." if input_data.moderators else "No specific moderators provided."
        
        # Build prompt based on single or multi-day event
        if input_data.start_date == input_data.end_date:
            prompt = (
                f"Using the theme: '{input_data.selected_theme}', provide a detailed descriptive agenda with timings "
                f"(from {input_data.start_time} to {input_data.end_time}), location, target audience, and purpose for the event on {input_data.start_date}. "
                f"It is a {input_data.event_type} event at {input_data.location}. "
                f"{moderators_str} "
                f"Additionally, draft a professional and concise email invitation content that includes the event title, "
                f"date, time, location, and a brief overview to invite participants."
            )
        else:
            prompt = (
                f"Using the theme: '{input_data.selected_theme}', provide a detailed descriptive agenda with timings "
                f"(from {input_data.start_time} to {input_data.end_time}), location, target audience, and purpose for the event "
                f"from {input_data.start_date} to {input_data.end_date}. "
                f"It is a {input_data.event_type} event at {input_data.location}. "
                f"{moderators_str} "
                f"Please make sure to split the agenda across both days ({input_data.start_date} and {input_data.end_date}), "
                f"showing a balanced distribution of sessions, breaks, and networking events for both days. "
                f"Additionally, draft a professional and concise email invitation content that includes the event title, "
                f"date range, daily timings, location, and a brief overview to invite participants."
            )
        
        try:
            response = completion(
                model=settings.model_name,
                messages=[{"content": prompt, "role": "user"}],
                api_base=settings.nim_base_url,
                api_key=settings.nim_api_key
            )
            
            # Safe extraction with proper None checks
            if response is None:
                raise ValueError("LLM returned None response")
            
            choices = response["choices"] if isinstance(response, dict) else None
            if not choices or len(choices) == 0:
                raise ValueError("LLM response has no choices")
            
            message = choices[0].get("message")
            if not message:
                raise ValueError("LLM response has no message")
            
            content = message.get("content")
            if not content:
                raise ValueError("LLM response has no content")
            
            refined_plan = content.strip()
            
            return EventPlanOutput(refined_plan=refined_plan)
            
        except Exception as e:
            print(f"Error refining event plan: {e}")
            # Return error message as fallback
            error_plan = f"""
# Event Planning Error

**Theme**: {input_data.selected_theme}
**Location**: {input_data.location}
**Date**: {input_data.start_date} to {input_data.end_date}
**Time**: {input_data.start_time} - {input_data.end_time}

## Error Details
Unable to generate event plan due to: {str(e)}

## Troubleshooting
1. Verify NIM_BASE_URL is set correctly: {settings.nim_base_url}
2. Check NVIDIA_API_KEY is valid
3. Ensure NVIDIA NIM endpoint is running and accessible
4. Check network connectivity
5. Verify model name: {settings.model_name}

Please check your configuration and try again.
"""
            return EventPlanOutput(refined_plan=error_plan)
    
    # Yield FunctionInfo to register the function with NeMo Agent Toolkit
    yield FunctionInfo.from_fn(
        _refine_plan,
        description="Transform a selected event theme into a detailed event plan with agenda, timings, and invitation"
    )


@register_function(config_type=FetchModeratorsConfig)
async def fetch_moderators(
    config: FetchModeratorsConfig,
    builder: Builder
):
    """
    Fetch moderator details from SQLite database.
    
    This function uses the FunctionInfo pattern required by NeMo Agent Toolkit.
    """
    
    async def _fetch_moderators(input_data: ModeratorsInput) -> ModeratorsOutput:
        """Inner function that fetches moderators from database."""
        moderators = db_manager.fetch_moderators_from_db(input_data.moderator_names)
        return ModeratorsOutput(moderators=moderators)
    
    # Yield FunctionInfo to register the function with NeMo Agent Toolkit
    yield FunctionInfo.from_fn(
        _fetch_moderators,
        description="Fetch moderator details from the database by name or get all moderators"
    )


@register_function(config_type=FetchParticipantsConfig)
async def fetch_participants(
    config: FetchParticipantsConfig,
    builder: Builder
):
    """
    Fetch participant details from SQLite database.
    
    This function uses the FunctionInfo pattern required by NeMo Agent Toolkit.
    """
    
    async def _fetch_participants(input_data: ParticipantsInput) -> ParticipantsOutput:
        """Inner function that fetches participants from database."""
        participants = db_manager.fetch_participants_from_db(
            participant_names=input_data.participant_names,
            limit=input_data.limit
        )
        return ParticipantsOutput(participants=participants)
    
    # Yield FunctionInfo to register the function with NeMo Agent Toolkit
    yield FunctionInfo.from_fn(
        _fetch_participants,
        description="Fetch participant details from the database by name or get all participants"
    )


# ==================== Standalone Usage (Without Config File) ====================

class EventPlanningWorkflow:
    """Standalone workflow class for direct Python usage (without CLI)."""
    
    def generate_event_themes(self, event_idea: str) -> List[str]:
        """Generate event themes synchronously."""
        prompt = (
            f"Generate exactly five professional, creative, and distinct event ideas "
            f"with titles and detailed descriptions based on: '{event_idea}'. "
            f"Format each theme as a numbered bold title followed by its description"
        )
        
        try:
            response = completion(
                model=settings.model_name,
                messages=[{"content": prompt, "role": "user"}],
                api_base=settings.nim_base_url,
                api_key=settings.nim_api_key
            )
            
            # Safe extraction with proper None checks
            if response is None:
                raise ValueError("LLM returned None response")
            
            choices = response["choices"] if isinstance(response, dict) else None
            if not choices or len(choices) == 0:
                raise ValueError("LLM response has no choices")
            
            message = choices[0].get("message")
            if not message:
                raise ValueError("LLM response has no message")
            
            content = message.get("content")
            if not content:
                raise ValueError("LLM response has no content")
            
            raw_response = content.strip()
            
            # Split themes by numbered format
            themes = re.split(r"\*\*\d+\.\s*", raw_response)
            if themes and not themes[0].strip():
                themes.pop(0)
            cleaned_themes = [theme.replace("\n\n", "\n").strip() for theme in themes if theme]
            
            return cleaned_themes if cleaned_themes else ["Error: Unable to generate themes"]
            
        except Exception as e:
            print(f"Error generating themes: {e}")
            return [f"Error generating themes: {str(e)}"]
    
    def start_event_planning(
        self,
        selected_theme: str,
        event_details: Dict[str, str],
        moderators: List[Dict[str, str]],
        participants: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Complete event planning workflow."""
        moderator_descriptions = " ".join([
            f"{moderator['name']} from {moderator['city']} with expertise in {moderator.get('description', 'events')}"
            for moderator in moderators
        ])
        moderators_str = f"The moderators for this event are: {moderator_descriptions}." if moderators else "No specific moderators provided."
        
        if event_details["start_date"] == event_details["end_date"]:
            prompt = (
                f"Using the theme: '{selected_theme}', provide a detailed descriptive agenda with timings "
                f"(from {event_details['start_time']} to {event_details['end_time']}), location, target audience, and purpose for the event on {event_details['start_date']}. "
                f"It is a {event_details['event_type']} event at {event_details['location']}. "
                f"{moderators_str} "
                f"Additionally, draft a professional and concise email invitation content."
            )
        else:
            prompt = (
                f"Using the theme: '{selected_theme}', provide a detailed descriptive agenda with timings "
                f"(from {event_details['start_time']} to {event_details['end_time']}), location, target audience, and purpose for the event "
                f"from {event_details['start_date']} to {event_details['end_date']}. "
                f"It is a {event_details['event_type']} event at {event_details['location']}. "
                f"{moderators_str} "
                f"Split the agenda across both days. Additionally, draft a professional email invitation."
            )
        
        try:
            response = completion(
                model=settings.model_name,
                messages=[{"content": prompt, "role": "user"}],
                api_base=settings.nim_base_url,
                api_key=settings.nim_api_key
            )
            
            # Safe extraction with proper None checks
            if response is None:
                raise ValueError("LLM returned None response")
            
            choices = response["choices"] if isinstance(response, dict) else None
            if not choices or len(choices) == 0:
                raise ValueError("LLM response has no choices")
            
            message = choices[0].get("message")
            if not message:
                raise ValueError("LLM response has no message")
            
            content = message.get("content")
            if not content:
                raise ValueError("LLM response has no content")
            
            plan = content.strip()
            
        except Exception as e:
            print(f"Error generating event plan: {e}")
            plan = f"Error generating plan: {str(e)}\nPlease check your LLM configuration."
        
        print("\n" + "="*60)
        print("REFINED EVENT PLAN")
        print("="*60)
        print(plan)
        print("="*60 + "\n")
        
        if participants:
            print("="*60)
            print("EVENT PARTICIPANTS")
            print("="*60)
            for p in participants:
                print(f"- {p.get('name', 'Unknown')} ({p.get('email', 'N/A')})")
            print("="*60 + "\n")
        
        return plan


if __name__ == "__main__":
    # Example: Direct Python usage (without NeMo CLI)
    planner = EventPlanningWorkflow()
    
    # Generate themes
    print("Generating themes...")
    themes = planner.generate_event_themes("pickle ball event")
    print(f"Generated {len(themes)} themes\n")
    
    # Fetch moderators from database
    moderators = db_manager.fetch_moderators_from_db()
    print(f"Found {len(moderators)} moderators in database")
    
    # Fetch participants from database
    participants = db_manager.fetch_participants_from_db(limit=10)
    print(f"Found {len(participants)} participants in database\n")
    
    # Create event plan
    if themes and moderators:
        event_details = {
            "start_date": "24-01-2025",
            "end_date": "25-01-2025",
            "start_time": "11:00 AM",
            "end_time": "5:00 PM",
            "location": "HYDERABAD",
            "event_type": "Technical Conference"
        }
        
        result = planner.start_event_planning(
            selected_theme=themes[0],
            event_details=event_details,
            moderators=moderators[:2] if len(moderators) > 2 else moderators,
            participants=participants
        )
        
        print("\n✅ Event planning completed successfully!")
    else:
        print("\n⚠️  No themes or moderators found. Please check your database.")