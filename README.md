# WealthAdvisorAI

An AI-powered multi-agent wealth advisory platform that guides financial advisors through a structured workflow to evaluate client portfolios and generate investment recommendations.

## Quick Start

This repository contains both:
- a FastAPI backend (`run_api.py`)
- a Streamlit frontend (`frontend/app.py`)
- a combined launcher (`run_app.py`) that starts both together

### Clone the repository

```bash
git clone https://github.com/AanishRahmani/WealthManagementAI.git
cd WealthAdvisorAI
```

### Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### Install dependencies

Using `pip`:

```bash
pip install -r requirements.txt
```

Using `uv`:

```bash
uv sync
```

> If you already use a `.venv`, make sure it is activated before running either command.

## Environment Setup

Create a `.env` file in the project root with your Hugging Face API token and model settings.

Example `.env`:

```env
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
HF_MODEL_ID=Qwen/Qwen2.5-7B-Instruct
```

## Run the App

### Option 1: Start both backend and frontend together

```bash
python run_app.py
```

This will launch:
- backend at `http://127.0.0.1:8081`
- frontend at `http://localhost:8501`

### Option 2: Start backend and frontend seperately only (Recommended for better debugging)

```bash
python run_api.py
```
## First time startup may take time to initialize DB 
Then visit:
- `http://127.0.0.1:8081/docs`
- to see the endpoints swagger UI

In a second terminal:

```bash
cd frontend
streamlit run app.py
```

Then visit:
- `http://localhost:8501`

## Recommended Workflow

1. Activate `.venv`
2. Install dependencies with `pip install -r requirements.txt` or `uv sync`
3. Create `.env` with your Hugging Face token
4. Run `python run_app.py`
5. Open the Streamlit interface at `http://localhost:8501`

## Project Structure

```
WealthAdvisorAI/
├──.env                 # Environment variables
├── app/                # FastAPI backend
│   ├── api/endpoints/  # REST API endpoints
│   ├── agents/         # Multi-agent logic
│   ├── core/           # Config, LLM, database helpers
│   ├── schemas/        # Pydantic models
│   └── services/       # Business logic
├── frontend/           # Streamlit frontend
│   ├── pages/
│   │   └── 1_Chat.py   # The chat interface
│   └── app.py          # Main frontend app
├── data/               # Local data stores
│   ├── db/
│   ├── chroma/
│   └── uploads/
├── run_api.py          # Backend entrypoint
├── run_app.py          # Launcher for both backend + frontend
├── requirements.txt    # Python dependencies
└── README.md
```

## Model Context Protocol (MCP) Integrations

The local chat agent dynamically fetches data via real-time tool loops using **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)**. The `MultiServerMCPClient` manages two independent dual streams seamlessly:

1. **SQLite Database Tooling (`mcp-sqlite`)**: Enables the agent to securely query schemas, index rows, and pull specific, raw backend `analysis_reports` directly.
2. **Second-Brain Memory (`chroma-mcp-server`)**: Empowers the AI to conduct sophisticated semantic text searches over the persistent vector storage directory (`data/chroma`) retaining long-term session histories and context.

## Usage Guide

### Stage 1: Client Profile Gathering
- Enter client information.
- Upload documents like PDF, CSV, XLSX, TXT, or DOCX.
- Add notes on client goals.
- Click `Initialize Analysis →`.

### Stage 2: Risk & Goals Assessment
- Answer assessment questions.
- Complete at least 70% of the workflow.
- Click `Generate Final Dashboard →` when ready.

### Stage 3: AI-Powered Analysis
- The backend runs three agents:
  - Portfolio Analysis Agent
  - Risk Assessment Agent
  - Recommendation Agent
- Review the results in the dashboard.

### Stage 4: Recommendation Scoring
- Inspect feasibility and impact scores.
- Review risk and projection metrics.
- Finalize the strategy.

### Stage 5: Portfolio Dashboard
- View portfolio metrics, charts, and client summaries.
- Export client reports as JSON.

## API Endpoints

### Upload
- `POST /v1/upload` — Upload portfolio documents and related files

### Client
- `POST /v1/clients/` — Create a new client entry
- `GET /v1/clients/dashboard` — Return array of client objects enriched with analysis payloads

### Assessment
- `GET /v1/assessment/next/{client_id}` — Fetch the next relevant assessment question
- `POST /v1/assessment/answer` — Submit an answer
- `GET /v1/assessment/status/{client_id}` — Get percentage coverage of profile assessment
- `GET /v1/assessment/profile/{client_id}` — Return complete assessment history log

### Analysis
- `GET /v1/analysis/run/{client_id}` — Orchestrates multiple AI agents to process risk, portfolio, and recommendations
- `POST /v1/analysis/save/{client_id}` — Allows frontend to explicitly save/overwrite an analysis state statically

### Chat
- `POST /v1/chat/session` — Spin up a persistent chat session thread
- `GET /v1/chat/sessions/{client_id}` — Retrieve all active chat sessions metadata for a client
- `GET /v1/chat/session/{session_id}` — Fetch metadata for a specific session wrapper
- `DELETE /v1/chat/session/{session_id}` — Permanently purge a chat session and its history
- `POST /v1/chat/send` — Send a prompt/message payload to the persistent agent
- `GET /v1/chat/messages/{session_id}` — Fetch chronological turn-by-turn conversational history array

### Dashboard
- `GET /v1/dashboard/client/{client_id}` — Get aggregate dashboard metrics for a single specific client
- `GET /v1/dashboard/all` — Aggregate metrics and score mappings across the entire firm


## Notes

- `run_app.py` is the easiest way to start both services together.
- If you want more control, run `run_api.py` and `streamlit run frontend/app.py` separately.
- Keep `.env` in the project root before starting the app.

## Testing / Utilities

This repository includes a few standalone scripts in the root directory for rapid local testing and debugging without needing to launch the entire UI stack:

- **`test_chat.py`**: A quick utility designed to test the FastAPI chat endpoints and ensure that localized prompts are successfully streaming or receiving payloads from the running server.
- **`test_sqlite.py`**: An identical testing script meant purely for isolating and establishing direct schema mappings with the SQLite database via `mcp-sqlite`. Use this to ensure your physical database file exists and is readable by the executable driver.
- **`test_chroma.py`**: A dedicated diagnostic script for validating the MCP architecture block. It safely spins up the `chroma-mcp-server` subprocess asynchronously, tests the dynamically constructed absolute paths via standard I/O streams, and prints out all the vector tooling dynamically exposed to Langchain (e.g. `chroma_create_collection`). Use this to ensure your Windows paths or virtual environment executable mappings aren't broken before booting the main app!

## License

This project is for educational and demonstration purposes.
