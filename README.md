AI Finance Agent (MVP)
1. What is this project?

This project is an AI Finance Agent (MVP) that helps users analyze financial data using natural language.

The system can:

Answer finance-related questions (stocks, crypto, portfolios)

Fetch read-only market data

Perform basic analysis and risk checks

Generate explainable reports (PDF/HTML)

Clearly state disclaimers and avoid any automated trading

⚠️ Important:
This system is not for executing trades or giving personalized financial advice.
All outputs are informational only.

2. High-level architecture (how the system works)

At a high level, the system follows a multi-agent architecture:

User
 ↓
Frontend (UI)
 ↓
Planner Agent
 ├── Data Agent → Market APIs / CSV
 ├── Analysis Agent → Metrics & Insights
 └── Risk Agent → Compliance & Disclaimers
 ↓
Report Generator
 ↓
User (Answer / Report)

Key components

Frontend

Chat interface

Portfolio CSV upload

Report viewer

Planner Agent

Understands user intent

Decides which agents/tools to call

Data Agent

Fetches market data

Loads portfolio CSVs

Normalizes and validates data

Analysis Agent

Computes metrics (returns, volatility, ratios)

Produces structured insights

Risk / Guardrails Agent

Blocks forbidden actions (e.g., trade execution)

Appends required disclaimers

Report Generator

Converts analysis into HTML/PDF reports

3. How to run the project locally
Prerequisites

Python 3.11+

Git

(Optional) make installed

Step-by-step setup
# Clone the repository
git clone <repo-url>
cd ai-finance-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
### Backend (Days 4-6)
```bash
# Run tests
pytest Tests/ -v

# Verify Day 4
python3 day4_verify.py

# Verify Day 5
python3 day5_verify.py

# Verify Day 6
python3 day6_verify.py
```

### Frontend (Day 7)
```bash
# Install dependencies
pip3 install streamlit pandas

# Run the Streamlit app
cd Frontend
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Features

### Current (Day 7)
- 💬 Chat interface for querying
- 📁 CSV portfolio upload
- 📊 Portfolio preview
- 🤖 Stub backend responses

### Coming Soon
- Day 8: LLM integration
- Day 9: Planner Agent
- Day 10: Analysis Agent
- Day 12: Full end-to-end workflow
Run tests
make test

Lint & format code
make lint
make format

4. Repository structure (where things live)
/frontend
  UI code (chat, uploads, report viewer)

/backend
  /agents      → AI agents (Planner, Data, Analysis, Risk)
  /data        → Data loaders, CSV handling, caching
  /services    → External APIs, report generation
  /core        → Shared utilities, configs, base classes

/infra
  Deployment, Docker, CI/CD related files

/tests
  Unit and integration tests

.github
  Issue templates, PR templates, workflows

Folder rules

No business logic in frontend

All AI logic lives in /backend/agents

Shared logic goes in /backend/core

Infra code must never leak into business logic

Development standards (locked decisions)

Backend language: Python

Python version: 3.11

API style: REST over HTTP

Formatter: Black

Linter: Ruff

Import sorting: isort

Naming conventions:

snake_case for functions & variables

PascalCase for classes

Contribution & conduct

Please read CONTRIBUTING.md before opening a PR

Follow the rules in CODE_OF_CONDUCT.md

Use the provided Issue and PR templates

Project status

🚧 Current phase: Project scaffolding & baseline
📅 Next step: CI setup + first Data Agent