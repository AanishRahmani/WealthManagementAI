"""
WealthAdvisorAI - Main Dashboard Application
Multi-stage investment advisory workflow with analysis and dashboard
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import time

# Configuration
API_BASE_URL = "http://localhost:8081/v1"

# Page configuration
st.set_page_config(
    page_title="Wealth Advisor AI - Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e3a5f;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stage-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2c5282;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        margin: 0.5rem 0;
    }
    .score-green {
        color: #38a169;
        font-weight: 700;
    }
    .score-amber {
        color: #dd6b20;
        font-weight: 700;
    }
    .score-red {
        color: #e53e3e;
        font-weight: 700;
    }
    .badge-implement {
        background-color: #38a169;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
    }
    .badge-strategic {
        background-color: #3182ce;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
    }
    .badge-quickwin {
        background-color: #dd6b20;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
    }
    .badge-monitor {
        background-color: #718096;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
    }
    .chat-message {
        background-color: #f7fafc;
        border-left: 4px solid #4299e1;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .stProgress > div > div > div > div {
        background-color: #4299e1;
    }
    .holding-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #e2e8f0;
    }
    .holding-ticker {
        font-weight: 600;
        color: #2d3748;
    }
    .holding-value {
        color: #4a5568;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'client_id' not in st.session_state:
    st.session_state.client_id = None
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = 1
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'assessment_answers' not in st.session_state:
    st.session_state.assessment_answers = {}
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None

# API Helper functions
def api_call(endpoint, method="get", data=None, files=None):
    """Make API call to FastAPI backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "get":
            response = requests.get(url)
        elif method == "post":
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# Sidebar navigation
with st.sidebar:
    st.title("🧭 Navigation")
    st.markdown("---")
    
    # Navigation buttons
    if st.button("🏠 App", use_container_width=True):
        st.session_state.current_stage = 1
        st.rerun()
    
    if st.button("💬 Chat", use_container_width=True):
        st.switch_page("pages/1_Chat.py")
    
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.current_stage = 5
        st.rerun()
    
    st.markdown("---")
    
    # Client info
    if st.session_state.client_id:
        st.markdown(f"**Client ID:** {st.session_state.client_id}")
        st.markdown(f"**Stage:** {st.session_state.current_stage}")
    else:
        st.markdown("No client selected")
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### Quick Actions")
    if st.button("Reset Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Main navigation
def main():
    # Header
    st.markdown('<h1 class="main-header">💼 Wealth Advisor AI</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Stage indicator
    stages = ["Profile", "Assessment", "Analysis", "Recommendations", "Dashboard"]
    cols = st.columns(5)
    for i, col in enumerate(cols):
        with col:
            if i + 1 == st.session_state.current_stage:
                st.markdown(f"**Stage {i+1}: {stages[i]}**")
            else:
                st.markdown(f"Stage {i+1}: {stages[i]}")
    
    st.markdown("---")
    
    # Route to appropriate page
    if st.session_state.current_stage == 1:
        show_client_profile()
    elif st.session_state.current_stage == 2:
        show_assessment()
    elif st.session_state.current_stage == 3:
        show_analysis()
    elif st.session_state.current_stage == 4:
        show_recommendations()
    elif st.session_state.current_stage == 5:
        show_dashboard()

# Stage 1: Client Profile
def show_client_profile():
    st.markdown('<h2 class="stage-header">Stage 1: Client Profile Gathering</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Client Information")
        client_name = st.text_input("Client Name", key="client_name")
        client_age = st.number_input("Age", min_value=18, max_value=100, value=65)
        portfolio_size = st.number_input("Portfolio Size ($)", min_value=0, value=2000000, step=100000)
        client_notes = st.text_area(
            "Client Notes & Goals",
            placeholder="e.g., Retired couple, income generation, reduce volatility, tax optimization...",
            height=150
        )
    
    with col2:
        st.markdown("### Document Upload")
        uploaded_file = st.file_uploader(
            "Upload Portfolio Statement",
            type=['pdf', 'txt', 'csv', 'xlsx', 'xls', 'docx'],
            help="Upload portfolio statements, financial documents, or investment reports"
        )
        
        if uploaded_file:
            st.session_state.uploaded_file_name = uploaded_file.name
            st.success(f"✅ {uploaded_file.name}")
    
    # Validation and continue button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Continue to Risk Assessment →", type="primary", use_container_width=True):
            # Validate: need either notes or file
            if not client_notes and not uploaded_file:
                st.error("Please provide notes or upload at least one document.")
            else:
                # Create client ID (use timestamp-based for demo)
                st.session_state.client_id = int(time.time() % 100000)
                
                # Upload file if provided
                if uploaded_file:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    data = {
                        "client_id": st.session_state.client_id,
                        "client_notes": client_notes
                    }
                    result = api_call("/upload", method="post", data=data, files=files)
                else:
                    data = {
                        "client_id": st.session_state.client_id,
                        "client_notes": client_notes
                    }
                    result = api_call("/upload", method="post", data=data)
                
                if result:
                    st.success("Client profile created successfully!")
                    st.session_state.current_stage = 2
                    st.rerun()

# Stage 2: Risk & Goals Assessment
def show_assessment():
    st.markdown('<h2 class="stage-header">Stage 2: Risk & Goals Assessment</h2>', unsafe_allow_html=True)
    
    if not st.session_state.client_id:
        st.error("No client ID found. Please go back to Stage 1.")
        return
    
    client_id = st.session_state.client_id
    
    # Get assessment status
    status = api_call(f"/assessment/status/{client_id}")
    completion = status.get("completion", 0) if status else 0
    can_advance = status.get("can_advance", False) if status else False
    missing = status.get("missing", []) if status else []
    
    # Progress bar
    st.markdown(f"**Assessment Completion: {completion}%**")
    st.progress(completion / 100)
    
    if can_advance:
        st.success("✅ Minimum 70% completion reached! You can proceed to analysis.")
    
    # Chat interface for questions
    st.markdown("### Assessment Questions")
    
    # Initialize chat messages
    if "assessment_messages" not in st.session_state:
        st.session_state.assessment_messages = []
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.assessment_messages:
            if msg["role"] == "assistant":
                st.markdown(f"""
                <div class="chat-message">
                    <strong>🤖 Advisor AI:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: right; margin: 0.5rem 0;">
                    <strong>You:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Get next question
    next_question = api_call(f"/assessment/next/{client_id}")
    
    if next_question and "id" in next_question:
        question_id = next_question["id"]
        question_text = next_question["text"]
        options = next_question.get("options", [])
        
        # Add question to chat if not already there
        if not st.session_state.assessment_messages or st.session_state.assessment_messages[-1]["role"] != "assistant":
            st.session_state.assessment_messages.append({
                "role": "assistant",
                "content": question_text
            })
        
        # Answer input
        if options:
            answer = st.radio(
                "Your answer:",
                options,
                key=f"q_{question_id}",
                horizontal=True
            )
        else:
            answer = st.text_input("Your answer:", key=f"q_{question_id}_text")
        
        if st.button("Submit Answer", key="submit_answer"):
            # Save answer
            api_call("/assessment/answer", method="post", data={
                "client_id": client_id,
                "question_id": question_id,
                "answer": answer
            })
            
            # Add to chat history
            st.session_state.assessment_messages.append({
                "role": "user",
                "content": answer
            })
            
            st.rerun()
    
    # Continue button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if can_advance:
            if st.button("Continue to Analysis →", type="primary", use_container_width=True):
                st.session_state.current_stage = 3
                st.rerun()
        else:
            st.button("Continue to Analysis →", type="secondary", use_container_width=True, disabled=True)
            st.info(f"Complete {len(missing)} more required questions to proceed.")

# Stage 3: AI Analysis
def show_analysis():
    st.markdown('<h2 class="stage-header">Stage 3: AI-Powered Analysis</h2>', unsafe_allow_html=True)
    
    if not st.session_state.client_id:
        st.error("No client ID found.")
        return
    
    client_id = st.session_state.client_id
    
    # Check if analysis already completed
    if st.session_state.analysis_result:
        st.success("✅ Analysis completed!")
        show_analysis_results(st.session_state.analysis_result)
    else:
        st.markdown("### Running AI Agents...")
        
        # Progress tracking
        progress_container = st.container()
        
        with progress_container:
            # Agent 1: Portfolio Analysis (25% weight)
            st.markdown("#### 📊 Agent 1: Portfolio Analysis (25%)")
            portfolio_progress = st.progress(0, text="Initializing...")
            portfolio_status = st.empty()
            
            # Simulate progress
            for i in range(0, 101, 5):
                portfolio_progress.progress(i, text=f"Analyzing portfolio... {i}%")
                time.sleep(0.1)
            
            portfolio_status.success("✅ Portfolio analysis complete!")
            
            # Agent 2: Risk Assessment (25% weight)
            st.markdown("#### ⚠️ Agent 2: Risk Assessment (25%)")
            risk_progress = st.progress(0, text="Initializing...")
            risk_status = st.empty()
            
            for i in range(0, 101, 5):
                risk_progress.progress(i, text=f"Assessing risks... {i}%")
                time.sleep(0.1)
            
            risk_status.success("✅ Risk assessment complete!")
            
            # Agent 3: Recommendation Agent (50% weight)
            st.markdown("#### 💡 Agent 3: Investment Recommendations (50%)")
            rec_progress = st.progress(0, text="Initializing...")
            rec_status = st.empty()
            
            for i in range(0, 101, 3):
                rec_progress.progress(i, text=f"Generating recommendations... {i}%")
                time.sleep(0.15)
            
            rec_status.success("✅ Recommendations generated!")
        
        # Run actual analysis
        with st.spinner("Finalizing analysis..."):
            result = api_call(f"/analysis/run/{client_id}")
            
            if result:
                st.session_state.analysis_result = result
                st.success("✅ Analysis completed successfully!")
                show_analysis_results(result)
            else:
                st.error("Analysis failed. Please try again.")
    
    # Continue button
    if st.session_state.analysis_result:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("View Recommendations →", type="primary", use_container_width=True):
                st.session_state.current_stage = 4
                st.rerun()

def show_analysis_results(result):
    """Display detailed analysis results"""
    st.markdown("### Analysis Results")
    
    # Create tabs for different analysis sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Portfolio", 
        "⚠️ Risk Analysis", 
        "💡 Recommendations",
        "📈 Holdings"
    ])
    
    with tab1:
        portfolio = result.get("portfolio_analysis", {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Documents Analyzed", portfolio.get("documents_analyzed", 0))
        with col2:
            st.metric("Holdings Identified", portfolio.get("holdings_identified", 0))
        with col3:
            st.metric("Asset Classes", portfolio.get("asset_classes_detected", 0))
        with col4:
            st.metric("Diversification Score", f"{portfolio.get('diversification_score', 0)}/100")
        
        # Asset Allocation Chart
        st.markdown("#### Asset Allocation")
        allocation = portfolio.get("allocation", {})
        if allocation:
            fig = px.pie(
                values=list(allocation.values()),
                names=list(allocation.keys()),
                title="Portfolio Asset Allocation",
                color_discrete_sequence=px.colors.sequential.Blues
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Sector Exposure Chart
        st.markdown("#### Sector Exposure")
        sector_exposure = portfolio.get("sector_exposure", {})
        if sector_exposure:
            fig = px.bar(
                x=list(sector_exposure.keys()),
                y=list(sector_exposure.values()),
                title="Sector Exposure (%)",
                labels={'x': 'Sector', 'y': 'Exposure (%)'},
                color=list(sector_exposure.values()),
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        risk = result.get("risk_analysis", {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Risk Score", f"{risk.get('overall_risk_score', 0)}/100")
        with col2:
            st.metric("Risk Level", risk.get("risk_level", "Unknown"))
        with col3:
            st.metric("Confidence", f"{risk.get('risk_confidence', 0):.0%}")
        
        # Risk Drivers
        st.markdown("#### Risk Drivers")
        drivers = risk.get("drivers", [])
        for driver in drivers:
            st.write(f"• {driver}")
        
        # Risk Issues
        st.markdown("#### Identified Issues")
        issues = risk.get("issues", [])
        for issue in issues:
            st.warning(f"⚠️ {issue}")
        
        # Recommended Actions
        st.markdown("#### Recommended Actions")
        actions = risk.get("recommended_actions", [])
        for action in actions:
            st.info(f"💡 {action}")
        
        # Risk Summary
        st.markdown("#### Risk Summary")
        st.write(risk.get("summary", "No summary available."))
    
    with tab3:
        rec = result.get("recommendations", {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Recommendations", rec.get("recommendations_generated", 0))
        with col2:
            st.metric("Expected Return Improvement", f"{rec.get('expected_return_improvement', 0)}%")
        with col3:
            st.metric("Implementation Cost", f"${rec.get('implementation_cost', 0):,.0f}")
        with col4:
            st.metric("Confidence", f"{rec.get('recommendation_confidence', 0):.0%}")
        
        # Strategy Focus
        st.markdown("#### Strategy Focus")
        st.write(rec.get("strategy_focus", "No strategy available."))
        
        # Actions
        st.markdown("#### Recommended Actions")
        actions = rec.get("actions", [])
        for action in actions:
            st.write(f"**Priority {action.get('priority')}**: {action.get('action')}")
            st.caption(f"→ {action.get('reason')}")
        
        # Projection
        projection = rec.get("projection", {})
        if projection:
            st.markdown("#### 10-Year Projection")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Conservative (4%)", f"${projection.get('low', 0):,.0f}")
            with col2:
                st.metric("Base Case (8%)", f"${projection.get('base', 0):,.0f}")
            with col3:
                st.metric("Optimistic (12%)", f"${projection.get('high', 0):,.0f}")
    
    with tab4:
        holdings = result.get("portfolio_analysis", {}).get("holdings", [])
        if holdings:
            # Create DataFrame for better display
            df = pd.DataFrame(holdings)
            df['value'] = df['value'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(df, use_container_width=True)

# Stage 4: Recommendations
def show_recommendations():
    st.markdown('<h2 class="stage-header">Stage 4: Recommendation Scoring & Decision</h2>', unsafe_allow_html=True)
    
    if not st.session_state.analysis_result:
        st.error("No analysis results found. Please complete Stage 3 first.")
        return
    
    result = st.session_state.analysis_result
    
    # Get dashboard data
    dashboard = api_call(f"/dashboard/client/{st.session_state.client_id}")
    
    if not dashboard:
        st.error("Failed to load dashboard data.")
        return
    
    # Scoring metrics
    feasibility = dashboard.get("feasibility_score", 0)
    impact = dashboard.get("impact_score", 0)
    decision = dashboard.get("decision", "Monitor")
    
    # Color coding
    def get_score_color(score):
        if score >= 75:
            return "green"
        elif score >= 50:
            return "amber"
        else:
            return "red"
    
    feasibility_color = get_score_color(feasibility)
    impact_color = get_score_color(impact)
    
    # Score cards
    st.markdown("### Decision Scores")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, {'#38a169' if feasibility_color == 'green' else '#dd6b20' if feasibility_color == 'amber' else '#e53e3e'} 0%, {'#2c5282' if feasibility_color == 'green' else '#744210' if feasibility_color == 'amber' else '#742a2a'} 100%);">
            <h3>Feasibility Score</h3>
            <p style="font-size: 2.5rem; font-weight: bold;">{feasibility:.0f}</p>
            <p>{'Easy to implement' if feasibility >= 75 else 'Moderate complexity' if feasibility >= 50 else 'Difficult/High barriers'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, {'#38a169' if impact_color == 'green' else '#dd6b20' if impact_color == 'amber' else '#e53e3e'} 0%, {'#2c5282' if impact_color == 'green' else '#744210' if impact_color == 'amber' else '#742a2a'} 100%);">
            <h3>Impact Score</h3>
            <p style="font-size: 2.5rem; font-weight: bold;">{impact:.0f}</p>
            <p>{'High impact' if impact >= 75 else 'Moderate impact' if impact >= 50 else 'Low impact'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Financial metrics
    st.markdown("### Financial Projections")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Projected Annual Return", f"{dashboard.get('projected_annual_return', 0)}%")
    with col2:
        st.metric("3-Year Projected Value", f"${dashboard.get('projected_value_3y', 0):,.0f}")
    with col3:
        st.metric("Implementation Cost", f"${dashboard.get('implementation_cost', 0):,.0f}")
    with col4:
        st.metric("Tax Implications", f"${dashboard.get('tax_implications', 0):,.0f}")
    
    # Agent findings
    st.markdown("### Agent Findings")
    agent_findings = dashboard.get("agent_findings", {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📊 Portfolio Analysis")
        portfolio = agent_findings.get("portfolio", {})
        st.write(f"- Allocation: {portfolio.get('allocation', {})}")
        st.write(f"- Sector Exposure: {portfolio.get('sector_exposure', {})}")
        st.write(f"- Diversification: {portfolio.get('diversification_score', 0)}/100")
    
    with col2:
        st.markdown("#### ⚠️ Risk Analysis")
        risk = agent_findings.get("risk", {})
        st.write(f"- Risk Level: {risk.get('risk_level', 'N/A')}")
        st.write(f"- Risk Score: {risk.get('overall_risk_score', 0)}/100")
        st.write(f"- Summary: {risk.get('summary', 'N/A')}")
    
    with col3:
        st.markdown("#### 💡 Recommendations")
        rec = agent_findings.get("recommendations", {})
        st.write(f"- Strategy: {rec.get('strategy_focus', 'N/A')}")
        st.write(f"- Actions: {rec.get('recommendations_generated', 0)} generated")
        st.write(f"- Summary: {rec.get('summary', 'N/A')}")
    
    # Decision and strategy naming
    st.markdown("---")
    st.markdown(f"### Decision: <span class='badge-{decision.lower().replace(' ', '')}'>{decision}</span>", unsafe_allow_html=True)
    
    strategy_name = st.text_input(
        "Strategy Name (if implementing)",
        placeholder="e.g., Retirement Income Rebalancing"
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Implement Strategy →", type="primary", use_container_width=True):
            if strategy_name:
                st.session_state.strategy_name = strategy_name
                st.session_state.current_stage = 5
                st.rerun()
            else:
                st.warning("Please enter a strategy name.")

# Stage 5: Dashboard
def show_dashboard():
    st.markdown('<h2 class="stage-header">Stage 5: Portfolio Dashboard</h2>', unsafe_allow_html=True)
    
    if not st.session_state.client_id:
        st.error("No client ID found.")
        return
    
    client_id = st.session_state.client_id
    
    # Tab navigation
    tab1, tab2, tab3 = st.tabs(["Portfolio Table", "Feasibility-Impact Matrix", "Chat Summary"])
    
    with tab1:
        show_portfolio_table()
    
    with tab2:
        show_matrix()
    
    with tab3:
        show_chat_summary()

def show_portfolio_table():
    """Show client portfolio table"""
    st.markdown("### Client Portfolio")
    
    # Get all clients
    clients = api_call("/dashboard/clients")
    
    if not clients:
        st.info("No clients found. Start by creating a new client profile.")
        return
    
    # Display as table
    for client in clients:
        with st.expander(f"Client {client['client_id']} - {client['decision']}", expanded=(client['client_id'] == st.session_state.client_id)):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Feasibility", f"{client['feasibility_score']:.0f}")
            with col2:
                st.metric("Impact", f"{client['impact_score']:.0f}")
            with col3:
                st.metric("Projected Return", f"{client['projected_annual_return']}%")
            with col4:
                st.metric("Cost", f"${client['implementation_cost']:,.0f}")
            
            # Decision badge
            decision = client.get('decision', 'Monitor')
            badge_class = f"badge-{decision.lower().replace(' ', '')}"
            st.markdown(f"**Decision:** <span class='{badge_class}'>{decision}</span>", unsafe_allow_html=True)
            
            # Actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("View Details", key=f"view_{client['client_id']}"):
                    st.session_state.client_id = client['client_id']
                    st.session_state.current_stage = 4
                    st.rerun()
            with col2:
                if st.button("Export Report", key=f"export_{client['client_id']}"):
                    export_client_report(client['client_id'])

def show_matrix():
    """Show feasibility-impact matrix"""
    st.markdown("### Feasibility-Impact Matrix")
    
    # Get matrix data
    matrix_data = api_call("/dashboard/matrix")
    
    if not matrix_data:
        st.info("No data available for matrix.")
        return
    
    # Create scatter plot
    df = pd.DataFrame(matrix_data)
    
    # Color by decision
    color_map = {
        "Implement": "green",
        "Strategic Review": "blue",
        "Quick Win": "orange",
        "Monitor": "gray"
    }
    
    fig = px.scatter(
        df,
        x='x',
        y='y',
        color='decision',
        color_discrete_map=color_map,
        hover_data=['label'],
        labels={'x': 'Feasibility Score', 'y': 'Impact Score'},
        title='Client Recommendations Matrix',
        width=800,
        height=600
    )
    
    # Add quadrant lines
    fig.add_hline(y=75, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=75, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Add quadrant labels
    fig.add_annotation(x=85, y=85, text="High Impact<br>High Feasibility", showarrow=False, font_size=10)
    fig.add_annotation(x=85, y=25, text="High Impact<br>Low Feasibility", showarrow=False, font_size=10)
    fig.add_annotation(x=25, y=85, text="Low Impact<br>High Feasibility", showarrow=False, font_size=10)
    fig.add_annotation(x=25, y=25, text="Low Impact<br>Low Feasibility", showarrow=False, font_size=10)
    
    st.plotly_chart(fig, use_container_width=True)

def show_chat_summary():
    """Show latest chat summary from dashboard"""
    st.markdown("### Latest Chat Summary")
    
    dashboard = api_call(f"/dashboard/client/{st.session_state.client_id}")
    
    if not dashboard:
        st.error("Failed to load dashboard data.")
        return
    
    summary = dashboard.get("latest_chat_summary", "")
    
    if summary:
        st.markdown(f"""
        <div class="chat-message">
            <strong>📝 Latest Chat Summary:</strong><br><br>
            {summary}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No chat summary available. Start a chat session to generate a summary.")
    
    # Option to start new chat
    if st.button("Start New Chat Session"):
        result = api_call("/chat/session", method="post", data={
            "client_id": st.session_state.client_id,
            "title": f"Session for Client {st.session_state.client_id}"
        })
        if result:
            st.session_state.chat_session_id = result.get("session_id")
            st.success("Chat session created!")
            st.rerun()

def export_client_report(client_id):
    """Export client report as JSON"""
    dashboard = api_call(f"/dashboard/client/{client_id}")
    
    if not dashboard:
        st.error("Failed to load client data.")
        return
    
    # Create report
    report = {
        "client_id": client_id,
        "generated_at": str(pd.Timestamp.now()),
        "dashboard": dashboard,
        "analysis": st.session_state.analysis_result
    }
    
    # Save to file
    report_json = json.dumps(report, indent=2)
    
    st.download_button(
        label="Download Report (JSON)",
        data=report_json,
        file_name=f"client_{client_id}_report.json",
        mime="application/json"
    )

# Run main app
if __name__ == "__main__":
    main()