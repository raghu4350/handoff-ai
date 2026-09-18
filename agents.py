# agents.py
# ---------
# Defines the two CrewAI agents for HandoffAI.
#
# AGENT 1: Intake & Analysis Agent
#   - Retrieves deal from SQLite
#   - Validates mandatory fields
#   - Identifies required skills
#   - Never invents business data
#
# AGENT 2: Delivery Planning Agent
#   - Checks resource availability
#   - Assesses project risk (rule-based)
#   - Creates structured project handoff
#   - Escalates high-risk cases to human manager
#
# HOW AGENTS WORK IN CrewAI:
#   Agent = Role + Goal + Backstory + Tools + LLM
#
#   The LLM (Mistral AI) is the brain.
#   The tools are the hands.
#   The backstory (from prompts.py) is the personality and rules.
#   The role and goal tell the agent what it is and what it must achieve.

import os
from dotenv import load_dotenv
from crewai import Agent, LLM

import litellm
litellm.cache = None          # Disable prompt caching
litellm.drop_params = True    # Drop unsupported params (e.g. cache_breakpoint) instead of erroring

from tools import intake_tools, delivery_tools
from prompts import INTAKE_AGENT_BACKSTORY, DELIVERY_AGENT_BACKSTORY

# ─────────────────────────────────────────
# LOAD ENVIRONMENT VARIABLES
# ─────────────────────────────────────────

# Load MISTRAL_API_KEY from .env file
load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    raise ValueError(
        "MISTRAL_API_KEY is not set.\n"
        "Please create a .env file with: MISTRAL_API_KEY=your_key_here\n"
        "Get your key from: https://console.mistral.ai"
    )

# ─────────────────────────────────────────
# LLM CONFIGURATION
# ─────────────────────────────────────────
#
# CrewAI uses LiteLLM internally to connect to LLM providers.
# LiteLLM supports Mistral using the "mistral/" prefix on the model name.
#
# HOW IT WORKS:
#   CrewAI Agent
#       ↓
#   LiteLLM (inside CrewAI)
#       ↓
#   Mistral AI API  (using MISTRAL_API_KEY)
#       ↓
#   mistral-large-latest model
#
# CHANGING THE MODEL:
#   Only change it here — in one place.
#   All agents share this same LLM object.

mistral_llm = LLM(
    model   = "mistral/open-mistral-nemo",
    api_key = MISTRAL_API_KEY,
    temperature = 0.1,   
)


# ─────────────────────────────────────────
# AGENT 1 — Intake & Analysis Agent
# ─────────────────────────────────────────

def create_intake_agent() -> Agent:
    """
    Create and return the Intake & Analysis Agent.

    This agent is responsible for:
    - Retrieving deal information from the database
    - Validating all mandatory project fields
    - Identifying required skills from project description
    - Flagging missing information and asking the user for it
    - Passing a validated summary to the Delivery Planning Agent

    Tools available: get_deal_details, check_requirements
    """
    return Agent(
        role = "Intake & Analysis Agent",

        goal = (
            "Retrieve complete deal information for the given client, "
            "validate all mandatory project fields, identify required skills, "
            "and produce a validated project summary ready for delivery planning. "
            "If any mandatory information is missing, clearly ask for it — never invent it."
        ),

        backstory = INTAKE_AGENT_BACKSTORY,

        tools = intake_tools,   # Only Tools 1 and 2 — defined in tools.py

        llm = mistral_llm,

        verbose = True,         # Print agent thinking + tool calls to terminal

        allow_delegation = False,  # This agent must do its own work, not delegate
    )


# ─────────────────────────────────────────
# AGENT 2 — Delivery Planning Agent
# ─────────────────────────────────────────

def create_delivery_agent() -> Agent:
    """
    Create and return the Delivery Planning Agent.

    This agent is responsible for:
    - Receiving validated project data from the Intake Agent
    - Checking resource/skill availability
    - Assessing project risk using business rules
    - Creating the structured project handoff in the database
    - Escalating high-risk projects to a human manager

    Tools available: check_resource_availability, create_project_handoff, escalate_to_manager
    """
    return Agent(
        role = "Delivery Planning Agent",

        goal = (
            "Using the validated project information from the Intake Agent, "
            "check resource availability, assess project risk, create a structured "
            "project handoff in the database, and escalate to a human manager if "
            "the risk is HIGH or if critical resources are unavailable."
        ),

        backstory = DELIVERY_AGENT_BACKSTORY,

        tools = delivery_tools,  # Only Tools 3, 4, and 5 — defined in tools.py

        llm = mistral_llm,

        verbose = True,

        allow_delegation = False,
    )


# ─────────────────────────────────────────
# STANDALONE TEST — Run: python agents.py
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("TESTING AGENT CREATION")
    print("=" * 55)

    print("\n[*] Creating Intake & Analysis Agent...")
    intake_agent = create_intake_agent()
    print(f"  Role  : {intake_agent.role}")
    print(f"  Tools : {[t.name for t in intake_agent.tools]}")
    print(f"  LLM   : {intake_agent.llm.model}")
    print("  [OK] Intake Agent created successfully.")

    print("\n[*] Creating Delivery Planning Agent...")
    delivery_agent = create_delivery_agent()
    print(f"  Role  : {delivery_agent.role}")
    print(f"  Tools : {[t.name for t in delivery_agent.tools]}")
    print(f"  LLM   : {delivery_agent.llm.model}")
    print("  [OK] Delivery Agent created successfully.")

    print("\n" + "=" * 55)
    print("[OK] BOTH AGENTS CREATED SUCCESSFULLY")
    print("     (No API call made — just agent object creation)")
    print("=" * 55)
