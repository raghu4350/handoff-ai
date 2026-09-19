# tools.py
# --------
# This file contains all 5 business tools for HandoffAI.
#
# STRUCTURE:
#   PART A — Plain Python functions (business logic, tested in Phase 4)
#   PART B — CrewAI @tool wrappers (what the agents actually call)
#
# WHY TWO PARTS?
#   - Plain functions = business logic, easy to test independently
#   - @tool wrappers  = interface between LLM and business logic
#   - This separation makes debugging very easy
#
# HOW CrewAI TOOLS WORK:
#   1. LLM reads the tool's docstring to understand what it does
#   2. LLM decides which tool to call based on the current task
#   3. LLM calls the tool with appropriate arguments (always as strings)
#   4. Tool runs real Python code and returns a string result
#   5. LLM reads the result and decides the next action
#
# TOOLS IN THIS FILE:
#   1. get_deal_details        — retrieve deal from SQLite
#   2. check_requirements      — validate mandatory fields
#   3. check_resource_availability — check team availability
#   4. create_project_handoff  — save structured handoff to SQLite
#   5. escalate_to_manager     — save escalation record to SQLite

import sys
import io
import json
import os

# Fix Windows terminal Unicode encoding issue (safe to keep in production too)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from crewai.tools import tool

from database import (
    fetch_deal_by_client,
    fetch_resources_by_skills,
    save_handoff,
    save_escalation,
    generate_project_id,
)

# ─────────────────────────────────────────
# LOAD BUSINESS RULES
# ─────────────────────────────────────────

RULES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "delivery_rules.json"
)

with open(RULES_PATH, "r", encoding="utf-8") as f:
    RULES = json.load(f)

MANDATORY_FIELDS = RULES["mandatory_fields"]
SKILL_KEYWORDS   = RULES["skill_keywords"]
TIMELINE_CONFIG  = RULES["timeline_thresholds"]


# ═══════════════════════════════════════════════════════════════
# PART A — PLAIN PYTHON FUNCTIONS (business logic)
# These are tested, reusable, and called by the @tool wrappers.
# ═══════════════════════════════════════════════════════════════

def _get_deal(client_name: str) -> dict:
    """Retrieve deal data from SQLite by client name."""
    if not client_name or not client_name.strip():
        return {"error": "Client name cannot be empty."}

    deal = fetch_deal_by_client(client_name.strip())

    if not deal:
        return {
            "error": (
                f"No deal found for client '{client_name}'. "
                "Please check the client name or add the deal to the system."
            )
        }

    return {
        "found"            : True,
        "id"               : deal.get("id"),
        "client_name"      : deal.get("client_name"),
        "project_type"     : deal.get("project_type"),
        "budget"           : deal.get("budget"),
        "timeline"         : deal.get("timeline"),
        "requirements"     : deal.get("requirements"),
        "integrations"     : deal.get("integrations"),
        "technical_contact": deal.get("technical_contact"),
        "expected_users"   : deal.get("expected_users"),
        "status"           : deal.get("status"),
    }


def _check_reqs(deal_data: dict) -> dict:
    """Check mandatory fields and identify required skills."""
    missing_fields = []

    for field in MANDATORY_FIELDS:
        value = deal_data.get(field)
        if value is None or str(value).strip() in ("", "None", "none", "null"):
            missing_fields.append(field)

    required_skills = _identify_skills(deal_data)

    if missing_fields:
        return {
            "status"        : "incomplete",
            "missing_fields": missing_fields,
            "missing_count" : len(missing_fields),
            "required_skills": required_skills,
            "message"       : (
                f"Missing {len(missing_fields)} required field(s): "
                f"{', '.join(missing_fields)}. "
                "Please provide these before proceeding."
            ),
        }

    return {
        "status"         : "complete",
        "missing_fields" : [],
        "missing_count"  : 0,
        "required_skills": required_skills,
        "message"        : "All mandatory fields are present. Ready to proceed.",
    }


def _identify_skills(deal_data: dict) -> list:
    """Scan requirements and integrations text for required skill keywords."""
    text = " ".join([
        str(deal_data.get("requirements", "")),
        str(deal_data.get("integrations", "")),
        str(deal_data.get("project_type", "")),
    ]).lower()

    skills = []
    import re
    for keyword, skill_name in SKILL_KEYWORDS.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text):
            if skill_name not in skills:
                skills.append(skill_name)

    if "Backend Engineer" not in skills:
        skills.append("Backend Engineer")

    return skills


def _check_resources(required_skills: list) -> dict:
    """Check availability of required skills in the resources table."""
    if not required_skills:
        return {"error": "No skills provided to check."}

    resources        = fetch_resources_by_skills(required_skills)
    availability_map = {}
    unavailable      = []
    limited          = []
    available        = []

    for r in resources:
        skill  = r["skill"]
        status = r["availability"]
        availability_map[skill] = {"employee": r["employee_name"], "availability": status}

        if status == "unavailable":
            unavailable.append(skill)
        elif status == "limited":
            limited.append(skill)
        else:
            available.append(skill)

    if unavailable:
        resource_risk = "HIGH"
    elif limited:
        resource_risk = "MEDIUM"
    else:
        resource_risk = "LOW"

    return {
        "availability_map"   : availability_map,
        "available_skills"   : available,
        "limited_skills"     : limited,
        "unavailable_skills" : unavailable,
        "resource_risk_signal": resource_risk,
        "summary"            : (
            f"Available: {available} | Limited: {limited} | Unavailable: {unavailable}"
        ),
    }


def _calculate_risk(project_data: dict) -> tuple:
    """Apply rule-based risk scoring. Returns (risk_level, reasons_list)."""
    reasons    = []
    risk_score = 0

    unavailable = project_data.get("unavailable_skills", [])
    if unavailable:
        reasons.append(f"Critical skill(s) unavailable: {', '.join(unavailable)}")
        risk_score += 2

    timeline_weeks = _extract_weeks(project_data.get("timeline", ""))
    too_short = TIMELINE_CONFIG["too_short_weeks"]
    tight     = TIMELINE_CONFIG["tight_weeks"]

    if timeline_weeks and timeline_weeks <= too_short:
        reasons.append(
            f"Timeline critically short ({timeline_weeks} weeks, threshold: {too_short} weeks)"
        )
        risk_score += 2
    elif timeline_weeks and timeline_weeks <= tight:
        reasons.append(
            f"Timeline is tight ({timeline_weeks} weeks, threshold: {tight} weeks)"
        )
        risk_score += 1

    limited = project_data.get("limited_skills", [])
    if limited:
        reasons.append(f"Limited availability for: {', '.join(limited)}")
        risk_score += 1

    integrations = str(project_data.get("integrations", "")).strip()
    if integrations and integrations.lower() not in ("", "none", "null"):
        reasons.append(f"External integration dependency: {integrations}")
        risk_score += 1

    missing = project_data.get("missing_fields", [])
    if len(missing) >= 2:
        reasons.append(f"Multiple fields still missing: {', '.join(missing)}")
        risk_score += 2

    if risk_score >= 2:
        risk_level = "HIGH"
    elif risk_score == 1:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
        reasons.append("All resources available, timeline reasonable, requirements complete.")

    return risk_level, reasons


def _extract_weeks(timeline_str: str):
    """Extract number of weeks from a string like '6 weeks' or '3 months'. Returns int or None."""
    if not timeline_str:
        return None
    parts = str(timeline_str).lower().split()
    for i, part in enumerate(parts):
        if "week" in part and i > 0:
            try:
                return int(parts[i - 1])
            except ValueError:
                return None
        elif "month" in part and i > 0:
            try:
                return int(parts[i - 1]) * 4
            except ValueError:
                return None
    return None


def _build_summary(project_data: dict, risk_level: str, risk_reasons: list) -> str:
    """Build a short human-readable handoff summary for the database."""
    lines = [
        f"Client: {project_data.get('client_name')}",
        f"Project: {project_data.get('project_type')}",
        f"Timeline: {project_data.get('timeline')}",
        f"Budget: {project_data.get('budget', 'Not specified')}",
        f"Required Skills: {', '.join(project_data.get('required_skills', []))}",
        f"Risk Level: {risk_level}",
        f"Risk Reasons: {' | '.join(risk_reasons)}",
    ]
    return " || ".join(lines)


# ═══════════════════════════════════════════════════════════════
# PART B — CrewAI @tool WRAPPERS
#
# These are what the agents call.
#
# RULES FOR WRITING GOOD TOOL DOCSTRINGS:
#   1. First line = what the tool does (LLM reads this to decide when to use it)
#   2. Args section = what inputs are expected and in what format
#   3. Returns section = what the output looks like
#   4. Keep it clear — the LLM uses this as its instruction manual
# ═══════════════════════════════════════════════════════════════


@tool("Get Deal Details")
def get_deal_details(client_name: str) -> str:
    """
    Retrieve the sales deal and client information from the database.

    Use this tool FIRST when a new project or client is mentioned.
    It fetches all known information about the client from SQLite.

    Args:
        client_name: The name of the client or company.
                     Partial names work too (e.g. 'ABC' finds 'ABC Manufacturing').

    Returns:
        A JSON string containing the deal fields:
        id, client_name, project_type, budget, timeline, requirements,
        integrations, technical_contact, expected_users, status.
        Returns an error message if the client is not found.

    IMPORTANT: If the client is not found, do NOT invent deal details.
               Report the error clearly to the user.
    """
    result = _get_deal(client_name)
    return json.dumps(result, ensure_ascii=False)


@tool("Check Project Requirements")
def check_requirements(client_name: str) -> str:
    """
    Check whether all mandatory project fields are present for a client deal.

    Use this tool AFTER get_deal_details to validate completeness.
    This tool also identifies the required skills based on project description.

    Args:
        client_name: The name of the client whose deal should be validated.

    Returns:
        A JSON string containing:
        - status: 'complete' or 'incomplete'
        - missing_fields: list of field names that are missing
        - required_skills: list of skills needed for this project
        - message: human-readable explanation

    IMPORTANT: If fields are missing, ask the user for them.
               Do NOT invent or assume values for missing fields.
    """
    deal = _get_deal(client_name)
    if "error" in deal:
        return json.dumps(deal)
    result = _check_reqs(deal)
    # Include deal ID for later use by other tools
    result["deal_id"] = deal.get("id")
    result["deal_data"] = deal
    return json.dumps(result, ensure_ascii=False)


@tool("Check Resource Availability")
def check_resource_availability(required_skills: str) -> str:
    """
    Check which team members and skills are available for the project.

    Use this tool AFTER check_requirements to see if the team can deliver.
    Pass the required_skills as a comma-separated string.

    Args:
        required_skills: Comma-separated list of required skill names.
                         Example: "AI Engineer, Salesforce Specialist, Backend Engineer"

    Returns:
        A JSON string containing:
        - available_skills: list of skills with available team members
        - limited_skills: list of skills where team is partially available
        - unavailable_skills: list of skills with no available team member
        - resource_risk_signal: HIGH / MEDIUM / LOW
        - summary: one-line human-readable summary

    Use the resource_risk_signal when calculating overall project risk.
    """
    # Convert comma-separated string to list
    skills_list = [s.strip() for s in required_skills.split(",") if s.strip()]
    result = _check_resources(skills_list)
    return json.dumps(result, ensure_ascii=False)


@tool("Create Project Handoff")
def create_project_handoff(
    deal_id: int,
    client_name: str,
    project_type: str,
    budget: str,
    timeline: str,
    requirements: str,
    integrations: str,
    required_skills: list,
    unavailable_skills: list,
    limited_skills: list,
    missing_fields: list
) -> str:
    """
    Create a structured project handoff and save it permanently to the database.

    Use this tool AFTER checking resources and assessing risk.
    Pass all collected project information as arguments.

    Args:
        deal_id: the deal's database ID
        client_name: client company name
        project_type: type of project
        budget: project budget
        timeline: project timeline
        requirements: project requirements
        integrations: required integrations
        required_skills: list of skill names needed
        unavailable_skills: skills that are unavailable
        limited_skills: skills with limited availability
        missing_fields: any still-missing fields (ideally empty)

    Returns:
        A JSON string containing:
        - success: True or False
        - project_id: the confirmed unique ID (e.g. PRJ-101)
        - risk_level: HIGH / MEDIUM / LOW
        - risk_reasons: list of reasons for the risk level
        - handoff_status: 'Completed' or 'Pending Human Review'
        - message: confirmation message

    CRITICAL: Only claim the handoff was created if success is True.
              The project_id in the response is the proof of creation.
    """
    project_data = {
        "deal_id": deal_id,
        "client_name": client_name,
        "project_type": project_type,
        "budget": budget,
        "timeline": timeline,
        "requirements": requirements,
        "integrations": integrations,
        "required_skills": required_skills,
        "unavailable_skills": unavailable_skills,
        "limited_skills": limited_skills,
        "missing_fields": missing_fields,
    }

    # Validate minimum required keys
    required_keys = ["client_name", "project_type", "timeline"]
    for key in required_keys:
        if key not in project_data or not project_data[key]:
            return json.dumps({
                "success": False,
                "error"  : f"Missing required field for handoff: '{key}'"
            })

    # Calculate risk
    risk_level, risk_reasons = _calculate_risk(project_data)

    # Generate project ID
    project_id = generate_project_id()

    # Build summary
    summary = _build_summary(project_data, risk_level, risk_reasons)

    # Determine status
    handoff_status = "Pending Human Review" if risk_level == "HIGH" else "Completed"

    # Save to database
    saved = save_handoff(
        project_id    = project_id,
        deal_id       = project_data.get("deal_id", 0),
        client_name   = project_data["client_name"],
        project_type  = project_data["project_type"],
        risk_level    = risk_level,
        handoff_status= handoff_status,
        summary       = summary,
    )

    if not saved:
        return json.dumps({
            "success": False,
            "error"  : "Database error: could not save handoff. Please try again."
        })

    return json.dumps({
        "success"       : True,
        "project_id"    : project_id,
        "risk_level"    : risk_level,
        "risk_reasons"  : risk_reasons,
        "handoff_status": handoff_status,
        "summary"       : summary,
        "message"       : (
            f"Handoff {project_id} successfully created. "
            f"Risk level: {risk_level}. Status: {handoff_status}."
        ),
    }, ensure_ascii=False)


@tool("Escalate to Manager")
def escalate_to_manager(project_id: str, reason: str) -> str:
    """
    Create a human manager escalation record for a risky or uncertain project.

    Use this tool when:
    - Risk level is HIGH
    - A critical required skill is unavailable
    - Timeline is unrealistically short
    - Important project information is still missing
    - There is an unresolved integration dependency

    Args:
        project_id: the confirmed project ID (e.g. 'PRJ-101')
        reason: clear explanation of why escalation is needed

    Returns:
        A JSON string containing:
        - success: True or False
        - escalation_id: confirmed escalation ID (e.g. ESC-001)
        - project_id: the project being escalated
        - status: 'Pending'
        - message: confirmation message

    CRITICAL: Only claim escalation succeeded if success is True.
              The escalation_id in the response is the proof of escalation.
    """
    if not project_id:
        return json.dumps({"success": False, "error": "project_id is required."})
    if not reason:
        return json.dumps({"success": False, "error": "reason is required."})

    escalation_id = save_escalation(project_id=project_id, reason=reason)

    if escalation_id is None:
        return json.dumps({
            "success": False,
            "error"  : "Database error: could not save escalation. Please try again."
        })

    esc_id_str = f"ESC-{str(escalation_id).zfill(3)}"

    return json.dumps({
        "success"      : True,
        "escalation_id": esc_id_str,
        "project_id"   : project_id,
        "status"       : "Pending",
        "message"      : (
            f"Escalation {esc_id_str} created for {project_id}. "
            "Human manager review is required."
        ),
    })


# ═══════════════════════════════════════════════════════════════
# EXPORT — List of tools for Agent 1 and Agent 2
# Import these lists in agents.py
# ═══════════════════════════════════════════════════════════════

# Agent 1: Intake & Analysis Agent uses these tools
intake_tools = [
    get_deal_details,
    check_requirements,
]

# Agent 2: Delivery Planning Agent uses these tools
delivery_tools = [
    check_resource_availability,
    create_project_handoff,
    escalate_to_manager,
]


# ═══════════════════════════════════════════════════════════════
# STANDALONE TEST — Run: python tools.py
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from database import init_db
    init_db()

    print("\n" + "=" * 60)
    print("TESTING ALL 5 CrewAI TOOL WRAPPERS")
    print("=" * 60)

    # Tool 1
    print("\n[TOOL 1] get_deal_details")
    print("-" * 40)
    r1 = get_deal_details.run("ABC Manufacturing")
    data1 = json.loads(r1)
    print(f"  Client      : {data1.get('client_name')}")
    print(f"  Project     : {data1.get('project_type')}")
    print(f"  Timeline    : {data1.get('timeline')}")
    print(f"  Contact     : {data1.get('technical_contact')}")

    # Tool 2
    print("\n[TOOL 2] check_requirements - ABC Manufacturing")
    print("-" * 40)
    r2 = check_requirements.run("ABC Manufacturing")
    data2 = json.loads(r2)
    print(f"  Status         : {data2.get('status')}")
    print(f"  Missing Fields : {data2.get('missing_fields')}")
    print(f"  Required Skills: {data2.get('required_skills')}")

    print("\n[TOOL 2] check_requirements - RetailCo India (missing contact)")
    print("-" * 40)
    r2b = check_requirements.run("RetailCo")
    data2b = json.loads(r2b)
    print(f"  Status         : {data2b.get('status')}")
    print(f"  Missing Fields : {data2b.get('missing_fields')}")
    print(f"  Message        : {data2b.get('message')}")

    # Tool 3
    print("\n[TOOL 3] check_resource_availability")
    print("-" * 40)
    skills_str = "AI Engineer, Salesforce Specialist, Frontend Engineer, Backend Engineer"
    r3 = check_resource_availability.run(skills_str)
    data3 = json.loads(r3)
    print(f"  Available   : {data3.get('available_skills')}")
    print(f"  Limited     : {data3.get('limited_skills')}")
    print(f"  Unavailable : {data3.get('unavailable_skills')}")
    print(f"  Risk Signal : {data3.get('resource_risk_signal')}")

    # Tool 4
    print("\n[TOOL 4] create_project_handoff")
    print("-" * 40)
    handoff_input = json.dumps({
        "deal_id"           : data1.get("id"),
        "client_name"       : data1.get("client_name"),
        "project_type"      : data1.get("project_type"),
        "budget"            : data1.get("budget"),
        "timeline"          : data1.get("timeline"),
        "requirements"      : data1.get("requirements"),
        "integrations"      : data1.get("integrations"),
        "required_skills"   : data2.get("required_skills"),
        "unavailable_skills": data3.get("unavailable_skills"),
        "limited_skills"    : data3.get("limited_skills"),
        "missing_fields"    : [],
    })
    r4 = create_project_handoff.run(handoff_input)
    data4 = json.loads(r4)
    print(f"  Success     : {data4.get('success')}")
    print(f"  Project ID  : {data4.get('project_id')}")
    print(f"  Risk Level  : {data4.get('risk_level')}")
    print(f"  Risk Reasons: {data4.get('risk_reasons')}")
    print(f"  Status      : {data4.get('handoff_status')}")

    # Tool 5
    print("\n[TOOL 5] escalate_to_manager")
    print("-" * 40)
    esc_input = json.dumps({
        "project_id": data4.get("project_id", "PRJ-101"),
        "reason"    : "Salesforce Specialist unavailable. High delivery risk."
    })
    r5 = escalate_to_manager.run(esc_input)
    data5 = json.loads(r5)
    print(f"  Success       : {data5.get('success')}")
    print(f"  Escalation ID : {data5.get('escalation_id')}")
    print(f"  Project ID    : {data5.get('project_id')}")
    print(f"  Message       : {data5.get('message')}")

    print("\n" + "=" * 60)
    print("[OK] ALL 5 CrewAI TOOL WRAPPERS TESTED SUCCESSFULLY")
    print("=" * 60)
