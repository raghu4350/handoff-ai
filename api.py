import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3

from database import get_connection, init_db
from crew import run_handoff_workflow

# Initialize DB on startup
init_db()

app = FastAPI(title="HandoffAI API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EvaluateRequest(BaseModel):
    deal_id: int

class NewDealRequest(BaseModel):
    client_name: str
    project_type: str
    timeline: str
    budget: str
    requirements: str
    integrations: str
    technical_contact: str
    expected_users: int = 100

@app.get("/api/deals")
def get_deals():
    """Fetch all available test scenarios (deals)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, client_name, project_type, timeline, budget, technical_contact, requirements, integrations, expected_users FROM deals")
        deals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return deals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import os

def save_deal_to_codebase(req: NewDealRequest):
    """Self-modify database.py to permanently inject this deal into the seed data."""
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.py")
        with open(db_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        insert_idx = -1
        for i, line in enumerate(lines):
            if "cursor.executemany" in line and "INSERT INTO deals" in lines[i+1]:
                for j in range(i-1, i-5, -1):
                    if "]" in lines[j]:
                        insert_idx = j
                        break
                break
                
        if insert_idx != -1:
            req_text = req.requirements.replace('"', '\\"').replace('\n', ' ')
            new_code = f'''            # Automatically added via Manual Sales Entry
            (
                "{req.client_name}",
                "{req.project_type}",
                "{req.budget}",
                "{req.timeline}",
                "{req_text}",
                "{req.integrations}",
                "{req.technical_contact}",
                {req.expected_users},
                "Qualified"
            ),\n'''
            lines.insert(insert_idx, new_code)
            with open(db_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
    except Exception as e:
        print("Failed to save to codebase:", e)

@app.post("/api/deals")
def create_deal(req: NewDealRequest):
    """Create a new manual deal in the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO deals (client_name, project_type, budget, timeline, requirements, integrations, technical_contact, expected_users)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (req.client_name, req.project_type, req.budget, req.timeline, req.requirements, req.integrations, req.technical_contact, req.expected_users)
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        
        # Save to database.py permanently
        save_deal_to_codebase(req)
        
        return {"success": True, "deal_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/deals/{deal_id}")
def delete_deal(deal_id: int):
    """Delete a deal from the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/records")
def clear_records():
    """Clear all handoffs and escalations history."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM handoffs")
        cursor.execute("DELETE FROM escalations")
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/records")
def get_records():
    """Fetch recent handoffs and escalations."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT project_id, client_name, risk_level, handoff_status, created_at FROM handoffs ORDER BY created_at DESC LIMIT 5")
        handoffs = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT id as esc_id, project_id, reason, status, created_at FROM escalations ORDER BY created_at DESC LIMIT 5")
        escalations = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return {"handoffs": handoffs, "escalations": escalations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import re

def parse_crewai_result(result: dict) -> dict:
    """Parse the raw CrewAI text to generate a clean UI verdict without false positives."""
    final_text = str(result.get("final_result", "")).lower()
    tasks_text = str(result.get("tasks_output", "")).lower()
    
    # 1. Check for missing critical info first
    if re.search(r"status:\s*incomplete", tasks_text) or re.search(r"status:\s*incomplete", final_text):
        result["custom_message"] = "Incomplete message. Deal is cancelled."
        result["custom_color"] = "amber"
        return result

    # 2. Check if the AI successfully extracted a risk level (meaning it processed the manual text successfully!)
    risk_match = re.search(r"risk\s*level:\s*\**\s*(high|medium|low)", final_text)
    if risk_match:
        risk_level = risk_match.group(1)
        if risk_level == "high":
            result["custom_message"] = "Expert is not available. Deal cancelled."
            result["custom_color"] = "rose"
        else:
            result["custom_message"] = "Resources confirmed. Handoff approved!"
            result["custom_color"] = "emerald"
        return result

    # 3. Fallback: If no risk level AND "not found" is in the text, it means it couldn't find a DB deal and there was no manual text provided
    if "client not found" in tasks_text or "not found" in final_text or "no deal found" in tasks_text:
        result["custom_message"] = "There is no deal according to your search."
        result["custom_color"] = "amber"
        return result

    # 4. Ultimate fallback
    if "escalat" in final_text or "unavailable" in final_text:
         result["custom_message"] = "Expert is not available."
         result["custom_color"] = "rose"
    else:
         result["custom_message"] = "Low risk and available to confirm the deal."
         result["custom_color"] = "emerald"
         
    return result

@app.post("/api/handoff/evaluate")
def evaluate_handoff(req: EvaluateRequest):
    """Run the CrewAI workflow for a specific deal ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deals WHERE id = ?", (req.deal_id,))
        deal = cursor.fetchone()
        conn.close()
        
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
            
        deal = dict(deal)
        prompt = (
            f"Please run the intake process for the client '{deal['client_name']}'."
        )
        
        result = run_handoff_workflow(prompt)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return parse_crewai_result(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RawEvaluateRequest(BaseModel):
    prompt: str

@app.post("/api/handoff/evaluate_raw")
def evaluate_handoff_raw(req: RawEvaluateRequest):
    """Run the CrewAI workflow using a raw, ad-hoc manual prompt."""
    try:
        if not req.prompt or not req.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
            
        result = run_handoff_workflow(req.prompt.strip())
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return parse_crewai_result(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount the static React frontend
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
os.makedirs(frontend_path, exist_ok=True)
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
