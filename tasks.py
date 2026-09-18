# tasks.py
# --------
# Defines the two tasks for HandoffAI.
#
# WHAT IS A TASK IN CrewAI?
#   A Task tells an agent exactly what it must DO and what it must PRODUCE.
#   It is the "work ticket" assigned to an agent.
#
#   Task = Description (what to do) + Expected Output (what to return) + Agent
#
# TASK FLOW:
#   Task 1 → Intake & Analysis Agent
#       ↓ output becomes context
#   Task 2 → Delivery Planning Agent
#       ↓
#   Final result
#
# WHY SEPARATE tasks.py FROM agents.py?
#   - Agents define WHO does the work (role, personality, tools)
#   - Tasks define WHAT work is done for a specific project
#   - Separation means the same agent can be given different tasks in future

from crewai import Task
from agents import create_intake_agent, create_delivery_agent


# ─────────────────────────────────────────
# TASK 1 — Project Intake & Validation
# Assigned to: Intake & Analysis Agent
# ─────────────────────────────────────────

def create_intake_task(user_input: str) -> Task:
    """
    Create and return Task 1: Project Intake & Validation.

    This task tells the Intake Agent to:
    1. Read the user's input to identify the client name
    2. Call get_deal_details to retrieve full deal data from SQLite
    3. Call check_requirements to validate all mandatory fields
    4. List any missing fields — do NOT invent values
    5. Identify the required skills for this project
    6. Produce a structured validated summary for the Delivery Agent

    Args:
        user_input: The raw text typed by the user in the Streamlit UI.
                    Example: "ABC Manufacturing signed an AI project. Salesforce integration. 6 weeks."

    Returns:
        A CrewAI Task object assigned to the Intake Agent.
    """
    intake_agent = create_intake_agent()

    description = f"""
You have received a new sales opportunity. Here is what the user provided:

USER INPUT:
{user_input}

YOUR JOB:
Step 1: Read the user input and identify the client name.
Step 2: Call the 'Get Deal Details' tool with the client name to retrieve full deal information.
Step 3: YOU MUST call the 'Check Project Requirements' tool with the client name to validate all mandatory fields and identify REQUIRED SKILLS.
Step 4: Review the results carefully:
        - If any mandatory fields are missing, list them clearly.
          Ask the user to provide them. Do NOT invent or assume values.
        - If all fields are present, confirm the project is ready for delivery planning.
Step 5: Output the required skills EXACTLY as returned by the 'Check Project Requirements' tool. Do NOT guess or add extra skills.
Step 6: Note any obvious early risks (tight timeline, complex integrations, etc.)

CRITICAL RULES:
- Never invent client name, budget, timeline, technical contact, or any other field.
- If the client is not found in the database, report this clearly.
- Only report what tools actually return. Do not add information from your own knowledge.
- You MUST use the 'Check Project Requirements' tool. Do NOT manually determine required skills.
"""

    expected_output = """
A structured project intake report containing:

1. CLIENT & DEAL INFORMATION
   - Deal ID (from database)
   - Client Name (from database)
   - Project Type (from database)
   - Budget (from database)
   - Timeline (from database)
   - Requirements (from database)
   - Integrations Required (from database)
   - Technical Contact (from database)
   - Expected Users (from database)

2. VALIDATION STATUS
   - Status: COMPLETE or INCOMPLETE
   - Missing Fields: [list if any] or None

3. REQUIRED SKILLS
   - List of skills identified from project requirements

4. EARLY RISK FLAGS
   - Any obvious risks observed at intake stage

5. READY FOR DELIVERY PLANNING
   - YES (if all mandatory fields present) or NO (if fields are missing)

If information is missing, end with a clear question asking the user to provide it.
"""

    return Task(
        description     = description,
        expected_output = expected_output,
        agent           = intake_agent,
    )


# ─────────────────────────────────────────
# TASK 2 — Delivery Planning & Handoff
# Assigned to: Delivery Planning Agent
# ─────────────────────────────────────────

def create_delivery_task(intake_task: Task) -> Task:
    """
    Create and return Task 2: Delivery Planning & Handoff Creation.

    This task tells the Delivery Agent to:
    1. Read the validated summary from Task 1 (passed via context)
    2. Call check_resource_availability for the required skills
    3. Assess project risk using the resource results
    4. Call create_project_handoff with all collected data
    5. If risk is HIGH → call escalate_to_manager
    6. Return the final structured handoff result

    Args:
        intake_task: The completed Task 1 object.
                     CrewAI passes its output to this task as context.

    Returns:
        A CrewAI Task object assigned to the Delivery Agent.
    """
    delivery_agent = create_delivery_agent()

    description = """
You have received a validated project summary from the Intake Agent (in your context).

YOUR JOB:
Step 1: Read the validated project information from the Intake Agent's output.
        Extract: client_name, project_type, budget, timeline, requirements,
                 integrations, technical_contact, expected_users, deal_id,
                 and required_skills.

Step 2: Call the 'Check Resource Availability' tool with the required skills
        as a comma-separated string.
        Example: "AI Engineer, Salesforce Specialist, Backend Engineer"

Step 3: Review resource availability results:
        - Note which skills are available, limited, or unavailable.
        - Use this to inform risk assessment.

Step 4: Call the 'Create Project Handoff' tool passing all project data as separate arguments:
        - deal_id (integer), client_name, project_type, budget, timeline
        - requirements, integrations
        - required_skills (list of strings)
        - unavailable_skills (list of strings from resource check)
        - limited_skills (list of strings from resource check)
        - missing_fields (list of strings, empty if intake was complete)

Step 5: The tool will return a project_id, risk_level, and handoff_status.
        ONLY report success if the tool confirms success: true.

Step 6: Check the risk_level from the handoff tool response:
        - If risk_level is HIGH → call the 'Escalate to Manager' tool
          passing the 'project_id' and a clear 'reason'.
        - If risk_level is MEDIUM or LOW → no escalation needed

CRITICAL RULES:
- Never claim "Handoff created" unless create_project_handoff returns success: true.
- Never claim "Escalation done" unless escalate_to_manager returns success: true.
- Never invent project IDs, escalation IDs, or risk levels.
- All values must come from tool responses.
"""

    expected_output = """
A structured project handoff report containing:

1. RESOURCE AVAILABILITY
   - Per skill: employee name and availability status (available / limited / unavailable)

2. RISK ASSESSMENT
   - Risk Level: HIGH / MEDIUM / LOW
   - Risk Reasons: [list of specific reasons]

3. PROJECT HANDOFF
   - Project ID: [confirmed by tool, e.g. PRJ-101]
   - Client: [name]
   - Project Type: [type]
   - Timeline: [timeline]
   - Budget: [budget]
   - Handoff Status: Completed OR Pending Human Review

4. ESCALATION (if risk is HIGH)
   - Escalation ID: [confirmed by tool, e.g. ESC-001]
   - Escalation Status: Pending
   - Reason: [clear reason for escalation]
   OR
   - Escalation: Not Required (if risk is LOW or MEDIUM)

5. RECOMMENDED NEXT ACTION
   - One clear sentence telling the delivery manager what to do next.
"""

    return Task(
        description     = description,
        expected_output = expected_output,
        agent           = delivery_agent,
        context         = [intake_task],   # ← Task 1's output is passed here automatically
    )


# ─────────────────────────────────────────
# STANDALONE TEST — Run: python tasks.py
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("TESTING TASK CREATION (no API call)")
    print("=" * 55)

    # Create tasks with a sample input
    sample_input = "ABC Manufacturing - AI customer support project, Salesforce integration, 6 weeks"

    print("\n[*] Creating Task 1: Project Intake & Validation...")
    task1 = create_intake_task(sample_input)
    print(f"  Task description preview : {task1.description[:80].strip()}...")
    print(f"  Assigned agent           : {task1.agent.role}")
    print(f"  Agent tools              : {[t.name for t in task1.agent.tools]}")
    print("  [OK] Task 1 created.")

    print("\n[*] Creating Task 2: Delivery Planning & Handoff...")
    task2 = create_delivery_task(intake_task=task1)
    print(f"  Task description preview : {task2.description[:80].strip()}...")
    print(f"  Assigned agent           : {task2.agent.role}")
    print(f"  Agent tools              : {[t.name for t in task2.agent.tools]}")
    print(f"  Context from             : {task2.context[0].agent.role}")
    print("  [OK] Task 2 created.")

    print("\n" + "=" * 55)
    print("[OK] BOTH TASKS CREATED SUCCESSFULLY")
    print("     Task 2 will receive Task 1 output as context.")
    print("=" * 55)
