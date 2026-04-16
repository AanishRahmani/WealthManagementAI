# WealthAdvisorAI

An AI-powered multi-agent wealth advisory platform that guides financial advisors through a structured workflow to evaluate client portfolios and generate investment recommendations.

## Features

- **Multi-Stage Workflow**: 5-stage advisory process from client profiling to dashboard analytics
- **AI-Powered Analysis**: Three specialized agents (Portfolio, Risk, Recommendation) analyze client data
- **Document Processing**: Support for PDF, CSV, Excel, DOCX, and TXT files
- **Risk Assessment**: Interactive chat-based questionnaire with progress tracking
- **Dashboard Analytics**: Feasibility-Impact matrix, client portfolio table, and chat summaries
- **Export Functionality**: Generate client reports in JSON format

## Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Frontend**: Streamlit
- **Database**: SQLite + ChromaDB (vector embeddings)
- **AI/ML**: LangChain, HuggingFace Qwen model
- **Visualization**: Plotly

## Project Structure

```
WealthAdvisorAI/
├── app/                    # FastAPI backend
│   ├── agents/            # Multi-agent system
│   ├── api/endpoints/     # REST API endpoints
│   ├── core/              # Configuration, LLM, databases
│   ├── services/          # Business logic services
│   └── schemas/           # Pydantic data models
├── frontend/              # Streamlit frontend
│   └── app.py            # Main Streamlit application
├── data/                  # Data storage
│   ├── db/               # SQLite database
│   ├── chroma/           # Vector database
│   └── uploads/          # Uploaded documents
├── run_api.py            # FastAPI server entry point
├── requirements.txt      # Python dependencies
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.12 or higher
- pip or uv for package management
- HuggingFace API token (for LLM access)

### Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:AanishRahmani/WealthManagementAI.git
   cd WealthAdvisorAI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or using uv:
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Configure environment**
   
   Create a `.env` file in the root directory:
   ```env
   HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
   HF_MODEL_ID=Qwen/Qwen2.5-7B-Instruct
   ```

4. **Run the backend server**
   ```bash
   python run_api.py
   ```
   The API will be available at `http://localhost:8081`

5. **Run the frontend (in a separate terminal)**
   ```bash
   cd frontend
   streamlit run app.py
   ```
   The frontend will be available at `http://localhost:8501`

## Usage Guide

### Stage 1: Client Profile Gathering
- Enter client information (name, age, portfolio size)
- Upload portfolio statements or financial documents
- Add notes about client goals and requirements
- Click "Continue to Risk Assessment"

### Stage 2: Risk & Goals Assessment
- Answer questions through the chat interface
- Complete at least 70% of required questions
- Progress is tracked automatically
- Click "Continue to Analysis" when ready

### Stage 3: AI-Powered Analysis
- Watch as three AI agents analyze the client data:
  - **Portfolio Analysis Agent** (25%): Analyzes holdings and diversification
  - **Risk Assessment Agent** (25%): Evaluates risk metrics and compliance
  - **Recommendation Agent** (50%): Generates personalized strategies
- Progress bars show real-time status
- Results displayed upon completion

### Stage 4: Recommendation Scoring
- View Feasibility and Impact scores with color coding
- Review financial projections and metrics
- Examine detailed agent findings
- Name your strategy and click "Implement"

### Stage 5: Portfolio Dashboard
- **Portfolio Table**: View all clients with decision badges
- **Feasibility-Impact Matrix**: Interactive scatter plot
- **Chat Summary**: Quick access to latest conversation summaries
- Export client reports as JSON files

## API Endpoints

### Upload
- `POST /v1/upload` - Upload documents and notes; also update client goals when `client_goals` is provided
- `POST /v1/clients` - Create a new client with UUID and goals

### Assessment
- `GET /v1/assessment/next/{client_id}` - Get next question
- `POST /v1/assessment/answer` - Submit answer
- `GET /v1/assessment/status/{client_id}` - Get completion status
- `GET /v1/assessment/profile/{client_id}` - Generate client profile

### Analysis
- `GET /v1/analysis/run/{client_id}` - Run full AI analysis

### Chat
- `POST /v1/chat/session` - Create chat session
- `GET /v1/chat/sessions/{client_id}` - List sessions
- `POST /v1/chat/send` - Send message
- `GET /v1/chat/messages/{session_id}` - Get messages

### Dashboard
- `GET /v1/dashboard/client/{client_id}` - Client dashboard data
- `GET /v1/dashboard/clients` - All clients overview
- `GET /v1/dashboard/matrix` - Feasibility-Impact matrix data

## Key Architecture Decisions

1. **Multi-Agent System**: Three specialized agents with weighted contributions (25%, 25%, 50%) provide comprehensive analysis
2. **Dual Database**: SQLite for structured data, ChromaDB for semantic document search
3. **Background Processing**: Queue-based document processing prevents blocking
4. **Session State**: Streamlit session state maintains workflow continuity
5. **REST API**: Clean separation between frontend and backend enables independent scaling

## Challenges & Solutions

### Challenge 1: Real-time Progress Tracking
**Solution**: Simulated progress bars with actual API calls provide responsive UX while backend processes data.

### Challenge 2: Chat Summary Integration
**Solution**: Dashboard directly queries SQLite for latest_chat_summary, avoiding redundant API calls.

### Challenge 3: Multi-stage Workflow State
**Solution**: Streamlit session state manages client_id and analysis results across pages.

## Future Improvements

1. **PDF Export**: Generate professional PDF reports with charts and formatting
2. **Real-time Updates**: WebSocket integration for live progress updates
3. **Multi-client Support**: Enhanced portfolio management for multiple clients
4. **Advanced Analytics**: More sophisticated risk metrics and projections
5. **Mobile Optimization**: Responsive design for tablet and mobile devices
6. **Authentication**: User authentication and client data isolation
7. **Performance**: Caching and optimization for 100+ concurrent clients

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and demonstration purposes.

## Support

For questions or issues, please contact the development team.