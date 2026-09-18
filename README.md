<div align="center">
  
  # 🚀 Handoff AI (Enterprise Edition)
  
  **An Autonomous AI Gateway for Sales-to-Delivery Workflows**
  
  Eliminate contract slippage instantly. A dual-LLM autonomous pipeline that intercepts sales contracts, analyzes live engineering capacity, and guarantees delivery—*before the deal is signed.*

  <br />

  ![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
  ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![CrewAI](https://img.shields.io/badge/CrewAI-FF5A5F?style=for-the-badge&logo=robot&logoColor=white)
  ![Mistral](https://img.shields.io/badge/Mistral_AI-222222?style=for-the-badge&logo=mistral&logoColor=white)
  ![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)

</div>

---

## 🛑 The Core Problem vs. 💡 The Solution

| The Sales & Delivery Disconnect | The Handoff AI Gateway |
| :--- | :--- |
| **Missing Information:** Deals are signed without defining a budget, users, or exact tech stack. | **Intercept & Validate:** The AI mathematically proves that all required fields are present before allowing the deal to proceed. |
| **Resource Blindness:** Sales sells an iOS App project when all iOS developers are already booked for the next 6 months. | **Live Database Sync:** The AI queries the live company database and cross-references required skills against real-time engineer capacity. |
| **Unrealistic Scopes:** Promising massive features in impossible 2-week timelines just to win a signature. | **Automated Risk Assessment:** Flags dangerous timelines and immediately halts risky deals. |
| **Wasted Tech Time:** Senior tech leads waste hours every week trying to decipher messy, unstructured sales notes. | **Autonomous Management:** The AI agents handle the entire review process in seconds, leaving engineers free to code. |

---

## 🗺️ Autonomous Execution Pipeline

```mermaid
graph TD;
    %% Styling
    classDef frontend fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    classDef agent fill:#3b0764,stroke:#a855f7,stroke-width:2px,color:#fff
    classDef logic fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#fff
    classDef fail fill:#7f1d1d,stroke:#f87171,stroke-width:2px,color:#fff
    classDef success fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#fff

    A[🖥️ Sales Rep Submits Deal in React UI]:::frontend -->|Sent to FastAPI| B(🕵️‍♂️ Agent 1: Intake Checker):::agent
    B -->|Scans DB for missing info| C{Is Data Complete?}:::logic
    
    C -->|No| D[❌ Deal Cancelled - Missing Info]:::fail
    C -->|Yes| E(👷‍♂️ Agent 2: Capacity Matcher):::agent
    
    E -->|Checks live SQLite DB for engineer availability| F{Are Engineers Free?}:::logic
    
    F -->|No| G[⚠️ High Risk - Expert Unavailable]:::fail
    F -->|Yes| H[✅ Approved - Deal Handed Off Successfully!]:::success
```

---

## 🤖 The AI Agents Explained (In Simple Terms)

This project uses **CrewAI** to manage multiple AI workers (agents). We use the highly advanced **Mistral AI** LLM to power their brains. Instead of one AI trying to do everything, we split the job into two specialized workers:

### 🕵️‍♂️ Agent 1: The Intake Agent (The Checker)
- **What it does:** It looks at the messy, raw, unstructured notes from the salesperson.
- **Its goal:** It ensures that no mandatory fields are missing. It checks if there is a budget, a timeline, and a clear project type. 
- **The Catch:** If *anything* is missing, it instantly halts the process and cancels the deal until the information is provided.

### 👷‍♂️ Agent 2: The Delivery Agent (The Planner)
- **What it does:** Once the data is verified, this agent looks at the live company database (SQLite). 
- **Its goal:** It finds out exactly what kind of engineers are needed for the project (e.g., Python, React, iOS). Then, it checks if those specific engineers actually have free time right now. 
- **The Catch:** If the engineers are booked, it flags the deal as **High Risk**. If they are free, it officially approves the handoff!

---

## 🏗️ Codebase Architecture & Tech Stack

This project is built using a modern, fully decoupled architecture:

> **The Brains (CrewAI + Mistral LLM)**  
> We use the `mistral/open-mistral-nemo` model for fast, highly accurate reasoning. The agents are given specific **Tools** (Python functions) that allow them to query the database directly. They don't guess—they look up real data.

> **The Backend (FastAPI + Python)**  
> A lightning-fast Python server that routes requests from the frontend, triggers the AI agents, and manages the database connections.

> **The Frontend (React.js + Tailwind CSS)**  
> A stunning, highly interactive single-page application (SPA). It uses glassmorphism design, real-time feedback, and dynamic routing to look professional and premium.

> **The Database (SQLite)**  
> A persistent, real-time database that stores live engineer availability, their tech skills, and complete deal history.

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

<br/>
<div align="center">
  <i>Built with ❤️ for Autonomous Delivery Workflows</i>
</div>
