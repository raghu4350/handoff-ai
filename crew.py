# crew.py
# -------
# This is the "director" file for HandoffAI.
#
# It connects:
#   - Agents (from agents.py)
#   - Tasks  (from tasks.py)
#   - CrewAI orchestration
#
# And exposes one clean function:
#   run_handoff_workflow(user_input) → dict
#
# This function is called by:
#   - app.py (Streamlit UI)
#   - This file's own __main__ block (for terminal testing)
#
# PROCESS: sequential
#   Task 1 (Intake) runs first → output passed to Task 2 (Delivery)
#   This mirrors the real-world Sales → Delivery handoff workflow.

import os
import sys
import json

from dotenv import load_dotenv
from crewai import Crew, Process

from database import init_db
from tasks import create_intake_task, create_delivery_task

# ─────────────────────────────────────────
# ENVIRONMENT SETUP
# ─────────────────────────────────────────

load_dotenv()  # Load MISTRAL_API_KEY from .env


def _check_env():
    """
    Verify MISTRAL_API_KEY is present before starting the workflow.
    Raises a clear error if the key is missing.
    """
    key = os.getenv("MISTRAL_API_KEY")
    if not key or key.strip() == "your_mistral_api_key_here":
        raise EnvironmentError(
            "\n[ERROR] MISTRAL_API_KEY is not set or is still the placeholder value.\n"
            "Please open your .env file and add your real Mistral API key.\n"
            "Get your key from: https://console.mistral.ai\n"
            "Example: MISTRAL_API_KEY=abc123xyz..."
        )


# ─────────────────────────────────────────
# MAIN WORKFLOW FUNCTION
# ─────────────────────────────────────────

def run_handoff_workflow(user_input: str) -> dict:
    """
    Run the full HandoffAI agentic workflow for a given user input.

    This function:
    1. Validates environment
    2. Initializes the database (creates tables + seed data if needed)
    3. Creates Task 1 (Intake) and Task 2 (Delivery)
    4. Assembles the Crew
    5. Runs the workflow (Task 1 → Task 2)
    6. Returns a structured result dict

    Args:
        user_input (str): The user's description of the sales opportunity.
                          Example: "ABC Manufacturing - AI support project, Salesforce, 6 weeks"

    Returns:
        dict with keys:
            success (bool)        : True if workflow completed without error
            intake_output (str)   : Full output from the Intake Agent
            delivery_output (str) : Full output from the Delivery Agent
            final_result (str)    : The final crew result (delivery agent's output)
            error (str)           : Error message if success is False
    """
    # ── Step 0: Validate environment ────────────────────────────
    try:
        _check_env()
    except EnvironmentError as e:
        return {"success": False, "error": str(e)}

    # ── Step 1: Initialize database ───────────────────────────────
    try:
        init_db()
    except Exception as e:
        return {"success": False, "error": f"Database initialization failed: {str(e)}"}

    # ── Step 2: Validate user input ───────────────────────────────
    if not user_input or not user_input.strip():
        return {
            "success": False,
            "error"  : "User input cannot be empty. Please describe the sales opportunity."
        }

    # ── Step 3: Create tasks ───────────────────────────────────────
    # Task 1: Intake & Validation
    # Task 2: Delivery Planning (receives Task 1 output as context)
    try:
        task1 = create_intake_task(user_input.strip())
        task2 = create_delivery_task(intake_task=task1)
    except Exception as e:
        return {"success": False, "error": f"Task creation failed: {str(e)}"}

    # ── Step 4: Assemble the Crew ──────────────────────────────────
    # Crew takes both agents and tasks.
    # Process.sequential = run tasks in order (Task 1 → Task 2)
    # verbose=True = show agent thinking in terminal (great for demos)
    try:
        crew = Crew(
            agents  = [task1.agent, task2.agent],
            tasks   = [task1, task2],
            process = Process.sequential,
            verbose = True,
        )
    except Exception as e:
        return {"success": False, "error": f"Crew assembly failed: {str(e)}"}

    # ── Step 5: Run the workflow ──────────────────────────────────
    # crew.kickoff() starts the agentic workflow.
    # This makes real API calls to Mistral AI.
    # It will take 30–90 seconds depending on API response time.
    try:
        print("\n" + "=" * 60)
        print("HANDOFFAI WORKFLOW STARTING")
        print("=" * 60)
        print(f"User Input: {user_input[:100]}...")
        print("=" * 60 + "\n")

        result = crew.kickoff()

        # CrewAI returns a CrewOutput object
        # .raw gives us the final string output
        final_output = result.raw if hasattr(result, "raw") else str(result)

        print("\n" + "=" * 60)
        print("HANDOFFAI WORKFLOW COMPLETE")
        print("=" * 60)

        return {
            "success"         : True,
            "final_result"    : final_output,
            "tasks_output"    : _extract_task_outputs(result),
            "error"           : None,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        
        # Phase 10: Friendly Error Mapping
        if "AuthenticationError" in error_msg or "401" in error_msg:
            error_msg = "Invalid Mistral API Key. Please check your .env file."
        elif "RateLimitError" in error_msg or "429" in error_msg:
            error_msg = "Mistral API rate limit exceeded. Please wait a moment and try again."
        elif "PermissionDeniedError" in error_msg or "403" in error_msg:
            error_msg = "This model is not available in your Mistral subscription tier."
        elif "ConnectionError" in error_msg or "Timeout" in error_msg or "10054" in error_msg:
            error_msg = "Network connection failed. Please check your internet connection."
        elif "Expecting value: line" in error_msg or "JSONDecodeError" in error_msg:
            error_msg = "The Mistral API returned an invalid response (possible 502 Bad Gateway). Please try clicking 'Analyze Deal' again."
            
        print(f"\n[ERROR] Workflow failed: {error_msg}")
        return {
            "success": False,
            "error"  : f"Workflow execution failed: {error_msg}"
        }


def _extract_task_outputs(crew_result) -> list:
    """
    Helper: Extract individual task outputs from the CrewOutput object.
    Returns a list of dicts: [{"agent": name, "output": text}, ...]

    CrewAI stores per-task outputs in crew_result.tasks_output.
    This is useful for the Streamlit UI to show each agent's work separately.
    """
    outputs = []
    try:
        if hasattr(crew_result, "tasks_output") and crew_result.tasks_output:
            for task_output in crew_result.tasks_output:
                outputs.append({
                    "agent" : getattr(task_output, "agent", "Unknown Agent"),
                    "output": getattr(task_output, "raw", str(task_output)),
                })
    except Exception:
        pass  # If extraction fails, the final_result is still usable
    return outputs


# ─────────────────────────────────────────
# TERMINAL TEST — Run: python crew.py
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("HANDOFFAI — TERMINAL TEST")
    print("=" * 60)

    # You can change this input to test different scenarios:
    #
    # Scenario 1 — Complete project (ABC Manufacturing):
    test_input = "ABC Manufacturing signed an AI customer support automation project. They need Salesforce integration, a 6-week MVP timeline, budget of Rs.12 lakh."

    # Scenario 2 — Missing info (RetailCo — missing technical contact):
    # test_input = "RetailCo India wants an e-commerce recommendation engine. 8 weeks, budget Rs.8 lakh."

    # Scenario 3 — Tight timeline (FinTech Startup):
    # test_input = "FinTech Startup needs a payment dashboard. Only 2 weeks. Budget Rs.5 lakh. Razorpay integration."

    print(f"\nTest Input: {test_input}")
    print("\n[*] Running full agentic workflow...\n")

    result = run_handoff_workflow(test_input)

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    if result["success"]:
        print("\n[OK] Workflow completed successfully!\n")

        # Show per-task outputs if available
        if result.get("tasks_output"):
            for i, task_out in enumerate(result["tasks_output"], 1):
                print(f"\n--- AGENT {i}: {task_out.get('agent', 'Agent')} ---")
                print(task_out.get("output", ""))
                print("-" * 50)

        print("\n--- FINAL DELIVERY OUTPUT ---")
        print(result["final_result"])

    else:
        print(f"\n[ERROR] Workflow failed.")
        print(f"Reason: {result['error']}")
        print("\nPlease check:")
        print("  1. MISTRAL_API_KEY is set in .env")
        print("  2. You are using Python 3.10, 3.11, or 3.12")
        print("  3. crewai is installed: pip show crewai")
