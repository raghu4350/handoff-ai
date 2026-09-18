# 🚀 Handoff AI (Enterprise Edition)
**Autonomous AI Gateway for Sales-to-Delivery Workflows**

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)

---

## 🛑 The Core Problem
In most IT agencies, there is a massive gap between the **Sales Team** (who want to close deals as fast as possible) and the **Delivery Team** (who actually have to write the code). 

This gap causes massive business failures:
- **Missing Information:** Deals are closed without defining a budget or specific requirements.
- **Resource Blindness:** Sales sells an iOS app project when all the iOS developers are busy for the next 6 months.
- **Unrealistic Scopes:** Promising massive features in impossible 2-week timelines.
- **Ruined Reputations:** Having to cancel a deal or delay a project immediately after signing it makes the company look highly unprofessional.
- **Wasted Tech Time:** Senior engineers waste hours every week reading messy sales notes instead of building software.

## 💡 The Solution
**Handoff AI** intercepts this broken process using an autonomous AI pipeline. Before a deal is officially handed over to the tech team, our AI pipeline reads the messy sales contract, queries the live engineering database, and mathematically proves whether the deal is safe to take or too risky to sign.

---

## 🗺️ How It Works (The Pipeline)

```mermaid
graph TD;
    A[Sales Rep Submits Deal in UI] -->|Sent to FastAPI| B(Agent 1: Intake Checker)
    B -->|Scans DB for missing info| C{Is Data Complete?}
    C -->|No| D[Deal Cancelled - Missing Info]
    C -->|Yes| E(Agent 2: Capacity Matcher)
    E -->|Checks live SQLite DB for engineer availability| F{Are Engineers Free?}
    F -->|No| G[High Risk - Expert Unavailable]
    F -->|Yes| H[Approved - Deal Handed Off Successfully!]
    
    style A fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    style B fill:#3b0764,stroke:#a855f7,stroke-width:2px,color:#fff
    style C fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#fff
    style D fill:#7f1d1d,stroke:#f87171,stroke-width:2px,color:#fff
    style E fill:#172554,stroke:#60a5fa,stroke-width:2px,color:#fff
    style F fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#fff
    style G fill:#7f1d1d,stroke:#f87171,stroke-width:2px,color:#fff
    style H fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#fff
```

---

## 🤖 The AI Agents Explained (In Simple Terms)

This project uses **CrewAI** to manage multiple AI workers (agents). We use the **Mistral AI** LLM to power their brains. 

Instead of one AI trying to do everything, we split the job into two specialized workers:

### 🕵️‍♂️ Agent 1: The Intake Agent (The Checker)
**What it does:** It looks at the messy, raw notes from the salesperson.
**Its goal:** It ensures that no mandatory fields are missing. It checks if there is a budget, a timeline, and a clear project type. If *anything* is missing, it instantly halts the process and cancels the deal until the information is provided.

### 👷‍♂️ Agent 2: The Delivery Agent (The Planner)
**What it does:** Once the data is verified, this agent looks at the live company database (SQLite). 
**Its goal:** It finds out exactly what kind of engineers are needed for the project (e.g., Python, React, iOS). Then, it checks if those specific engineers actually have free time right now. If the engineers are booked, it flags the deal as **High Risk**. If they are free, it officially approves the handoff!

---

## 🏗️ Codebase Architecture & Tech Stack

This project is built using a modern, fully decoupled architecture:

1. **The Brains (CrewAI + Mistral LLM)**
   - We use the `mistral/open-mistral-nemo` model for fast, highly accurate reasoning.
   - The agents are given specific **Tools** (Python functions) that allow them to query the database directly. They don't guess—they look up real data.

2. **The Backend (FastAPI + Python)**
   - A lightning-fast Python server that routes requests from the frontend, triggers the AI agents, and manages the database connections.

3. **The Frontend (React.js + Tailwind CSS)**
   - A stunning, highly interactive single-page application (SPA). It uses glassmorphism design, real-time feedback, and dynamic routing to look professional and premium.

4. **The Database (SQLite)**
   - A persistent, real-time database that stores:
     - Engineer availability and skills.
     - Deal history (Approved, Cancelled, Escalated).

---

## 🚀 How to Run Locally

1. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

2. **Add API Key**
   Create a `.env` file in the root directory and add your Mistral API Key:
   ```env
   MISTRAL_API_KEY=your_key_here
   ```

3. **Start the Server**
   ```bash
   uvicorn api:app --reload --port 8501
   ```

4. **Open the App**
   Navigate to `http://localhost:8501` in your browser.
