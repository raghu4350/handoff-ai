# database.py
# -----------
# This file handles everything related to our SQLite database.
# It creates tables, inserts sample data, and provides
# simple helper functions for reading and writing records.
import sys
import io
# Fix Windows terminal Unicode issues
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
#
# Think of this file as the "store manager":
# - It sets up the shelves (CREATE TABLE)
# - Stocks them with starter items (seed data)
# - Lets other files put things in or take things out (CRUD helpers)

import sqlite3
import os
from datetime import datetime

# ─────────────────────────────────────────
# DATABASE FILE PATH
# ─────────────────────────────────────────

# handoff.db will be created in the same folder as this file.
# If the file already exists, it just opens it (no data loss).
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "handoff.db")


def get_connection():
    """
    Open and return a connection to the SQLite database.

    We set check_same_thread=False so Streamlit (which uses
    multiple threads) can use the same connection safely.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # This makes rows behave like dicts: row["client_name"] instead of row[0]
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────
# CREATE TABLES
# ─────────────────────────────────────────

def create_tables():
    """
    Create all 4 tables if they don't already exist.
    'IF NOT EXISTS' means running this twice won't cause errors.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # TABLE 1: deals
    # Stores Sales opportunity / client deal information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name       TEXT NOT NULL,
            project_type      TEXT,
            budget            TEXT,
            timeline          TEXT,
            requirements      TEXT,
            integrations      TEXT,
            technical_contact TEXT,
            expected_users    INTEGER,
            status            TEXT DEFAULT 'Qualified'
        )
    """)

    # TABLE 2: resources
    # Stores team member information and their availability
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name   TEXT NOT NULL,
            skill           TEXT NOT NULL,
            availability    TEXT NOT NULL
        )
    """)

    # TABLE 3: handoffs
    # Stores the final structured project handoff created by Agent 2
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS handoffs (
            project_id      TEXT PRIMARY KEY,
            deal_id         INTEGER,
            client_name     TEXT,
            project_type    TEXT,
            risk_level      TEXT,
            handoff_status  TEXT DEFAULT 'Completed',
            summary         TEXT,
            created_at      TEXT
        )
    """)

    # TABLE 4: escalations
    # Stores manager escalation records for high-risk projects
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id  TEXT NOT NULL,
            reason      TEXT NOT NULL,
            status      TEXT DEFAULT 'Pending',
            created_at  TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("[OK] All tables created successfully.")


# ─────────────────────────────────────────
# SEED DATA — Sample records for demo/testing
# ─────────────────────────────────────────

def seed_data():
    """
    Insert sample data only if the tables are empty.
    This prevents duplicate data every time you restart the app.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── SEED DEALS ──────────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) FROM deals")
    if cursor.fetchone()[0] == 0:

        sample_deals = [
            # Deal 1: Complete deal — all fields present
            # Expected: MEDIUM or HIGH risk (Salesforce unavailable)
            (
                "ABC Manufacturing",
                "AI Customer Support Automation",
                "₹12,00,000",
                "6 weeks",
                "Build an AI-powered customer support assistant with automated ticket resolution",
                "Salesforce",
                "Rohan Sharma",
                500,
                "Qualified"
            ),
            # Deal 2: Missing technical_contact — triggers missing info scenario
            (
                "RetailCo India",
                "E-commerce Recommendation Engine",
                "₹8,00,000",
                "8 weeks",
                "Build a product recommendation system using ML for their e-commerce platform",
                "None",
                None,           # technical_contact is missing → Agent 1 should catch this
                200,
                "Qualified"
            ),
            # Deal 3: Extremely tight timeline — triggers HIGH risk
            (
                "FinTech Startup",
                "Payment Dashboard",
                "₹5,00,000",
                "2 weeks",  # Too short → HIGH risk timeline rule triggers
                "Build a real-time payment tracking dashboard with API integrations",
                "Razorpay",
                "Karan Mehta",
                50,
                "Qualified"
            ),
            # Deal 4: Interview Showcase (Honda Mobile App)
            (
                "Honda",
                "Mobile App",
                "$50,000",
                "3 Months", 
                "Build a modern customer-facing mobile application for iOS",
                "Honda CRM",
                "Sanjay Gupta",
                10000,
                "Qualified"
            ),
            # Deal 5: The "Perfect" Deal (Low Risk, Available Resources)
            (
                "TechCorp",
                "Backend Data Processing API",
                "₹15,00,000",
                "12 weeks",
                "Build a highly scalable backend API using Python and AI models for data processing",
                "None",
                "Priya Sharma",
                1000,
                "Qualified"
            ),
            # Automatically added via Manual Sales Entry
            (
                "pg innovation",
                "video editing",
                "500000",
                "2months",
                "helloo",
                "None",
                "raghav",
                100,
                "Qualified"
            ),
        ]

        cursor.executemany("""
            INSERT INTO deals
            (client_name, project_type, budget, timeline, requirements,
             integrations, technical_contact, expected_users, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_deals)

        print("[OK] Sample deals inserted.")

    # ── SEED RESOURCES ───────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) FROM resources")
    if cursor.fetchone()[0] == 0:

        sample_resources = [
            ("Amit Kumar", "AI Engineer",          "available"),
            ("Neha Singh", "Backend Engineer",      "available"),
            ("Raj Patel",  "Frontend Engineer",     "limited"),
            ("Priya Nair", "Salesforce Specialist", "unavailable"),
            ("Anjali Desai", "iOS Developer",       "unavailable"), # Triggers the Honda Escalation
        ]

        cursor.executemany("""
            INSERT INTO resources (employee_name, skill, availability)
            VALUES (?, ?, ?)
        """, sample_resources)

        print("[OK] Sample resources inserted.")

    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# HELPER FUNCTIONS — Used by tools.py
# ─────────────────────────────────────────

def fetch_deal_by_client(client_name: str):
    """
    Search for a deal by client name (case-insensitive partial match).
    Returns a dict if found, or None if not found.

    Example:
        fetch_deal_by_client("ABC") → returns ABC Manufacturing's deal
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM deals
        WHERE LOWER(client_name) LIKE LOWER(?)
        LIMIT 1
    """, (f"%{client_name}%",))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def fetch_resources_by_skills(skills: list) -> list:
    """
    Look up availability for a list of skill names.
    Returns a list of resource dicts.

    Example:
        fetch_resources_by_skills(["AI Engineer", "Salesforce Specialist"])
        → [{"skill": "AI Engineer", "availability": "available"}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()

    results = []
    for skill in skills:
        cursor.execute("""
            SELECT employee_name, skill, availability
            FROM resources
            WHERE LOWER(skill) LIKE LOWER(?)
            LIMIT 1
        """, (f"%{skill}%",))
        row = cursor.fetchone()
        if row:
            results.append(dict(row))
        else:
            # Skill not found in database = treat as unavailable
            results.append({
                "employee_name": "Unassigned",
                "skill": skill,
                "availability": "unavailable"
            })

    conn.close()
    return results


def save_handoff(project_id: str, deal_id: int, client_name: str,
                 project_type: str, risk_level: str,
                 handoff_status: str, summary: str) -> bool:
    """
    Save a completed project handoff to the handoffs table.
    Returns True on success, False on failure.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO handoffs
            (project_id, deal_id, client_name, project_type,
             risk_level, handoff_status, summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            deal_id,
            client_name,
            project_type,
            risk_level,
            handoff_status,
            summary,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error saving handoff: {e}")
        return False
    finally:
        conn.close()


def save_escalation(project_id: str, reason: str):
    """
    Save a manager escalation record.
    Returns the new escalation ID on success, None on failure.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO escalations (project_id, reason, status, created_at)
            VALUES (?, ?, 'Pending', ?)
        """, (
            project_id,
            reason,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        escalation_id = cursor.lastrowid  # Auto-generated ID
        return escalation_id
    except Exception as e:
        print(f"❌ Error saving escalation: {e}")
        return None
    finally:
        conn.close()


def generate_project_id() -> str:
    """
    Generate a unique project ID like PRJ-101, PRJ-102, etc.
    Based on how many handoffs already exist in the database.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM handoffs")
    count = cursor.fetchone()[0]
    conn.close()
    return f"PRJ-{str(count + 101).zfill(3)}"


# ─────────────────────────────────────────
# INITIALIZE DATABASE
# ─────────────────────────────────────────

def init_db():
    """
    Main function to initialize the database.
    Call this once when the app starts.
    """
    print("[*] Initializing database...")
    create_tables()
    seed_data()
    print("[OK] Database ready.")


# ─────────────────────────────────────────
# RUN DIRECTLY TO TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    # Run: python database.py
    # Creates DB and prints all records to verify.

    init_db()

    print("\n" + "=" * 50)
    print("VERIFYING DATA")
    print("=" * 50)

    conn = get_connection()
    cursor = conn.cursor()

    print("\nDEALS TABLE:")
    cursor.execute("SELECT id, client_name, project_type, timeline, budget, technical_contact FROM deals")
    for row in cursor.fetchall():
        print(f"  ID:{row['id']} | {row['client_name']} | {row['project_type']} | "
              f"{row['timeline']} | {row['budget']} | Contact: {row['technical_contact']}")

    print("\nRESOURCES TABLE:")
    cursor.execute("SELECT employee_name, skill, availability FROM resources")
    for row in cursor.fetchall():
        icon = "[OK]" if row['availability'] == "available" else ("[!!]" if row['availability'] == "limited" else "[X]")
        print(f"  {icon} {row['employee_name']} | {row['skill']} | {row['availability']}")

    print("\nHANDOFFS TABLE (empty until workflow runs):")
    cursor.execute("SELECT * FROM handoffs")
    print(f"  {len(cursor.fetchall())} handoff(s) found.")

    print("\nESCALATIONS TABLE (empty until workflow runs):")
    cursor.execute("SELECT * FROM escalations")
    print(f"  {len(cursor.fetchall())} escalation(s) found.")

    conn.close()
    print("\n[OK] Database verification complete.")
