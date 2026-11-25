# HackEventHub.ai

HackEventHub.ai is a personal opportunity discovery platform for finding hackathons, conferences, workshops, and other events in one place.

It collects opportunities from registered websites, evaluates them against your interests, and presents the results through a web dashboard and optional Telegram notifications.

## Features

- Register and manage event and hackathon sources
- Crawl websites and collect opportunity listings
- Filter opportunities by topic, city, online availability, and price
- Score opportunities against personal interests
- Save or hide opportunities for later review
- View crawl history, discovered items, and provider activity
- Chat with an AI assistant about collected opportunities
- Choose between Ollama, Azure OpenAI, and Athena providers
- Receive scheduled or instant Telegram alerts

## Tech stack

- Backend: Python, FastAPI, SQLModel, Alembic
- Frontend: React, TypeScript, Vite, Tailwind CSS
- Database: SQLite by default
- Integrations: Telegram, TinyFish, configurable LLM providers

## Project structure

```text
app/                 FastAPI application, database models, services, and Telegram bot
frontend/            React dashboard
alembic/             Database migrations
tests/               Backend and integration tests
scripts/             Development and contract-test scripts
presets.example.json Example source presets
```

## Requirements

- Python 3.11 or newer
- Node.js 18 or newer
- npm

## Quick start

### 1. Configure the backend

Create a local environment file from the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and add any LLM, TinyFish, or Telegram credentials you want to use.

### 2. Install backend dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 3. Install frontend dependencies

```powershell
Set-Location frontend
npm install
```

### 4. Start the application

From the project root:

```powershell
.\scripts\start.ps1
```

The dashboard is served at `http://localhost:8000` when the production frontend has been built. During frontend development, run:

```powershell
Set-Location frontend
npm run dev
```

## Useful commands

Build the frontend:

```powershell
Set-Location frontend
npm run build
```

Run the test suite:

```powershell
pytest
```

Run linting:

```powershell
ruff check .
```

## API and dashboard

When the backend is running, FastAPI documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

The dashboard provides pages for the overview, source registry, opportunities, LLM providers, preferences, crawl logs, and agent chat.

## Environment and data

Local secrets are stored in `.env` and are excluded from Git. The default SQLite database and runtime data are also excluded from commits. Use `.env.example` as the safe configuration reference.

## License

This project is currently provided for personal and educational use. Add a formal license before distributing it as an open-source project.
