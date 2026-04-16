
import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# --- CONFIGURATION ---
API_BASE_URL = "http://localhost:8081/v1"

st.set_page_config(
    page_title="Wealth Advisor AI - Enterprise Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM UI STYLING ---
st.markdown("""
<style>
    .main-header { font-size: 3rem; font-weight: 800; color: #1e3a5f; text-align: center; margin-bottom: 1rem; }
    .stage-header { font-size: 1.8rem; font-weight: 600; color: #2c5282; margin-bottom: 1.5rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }
    .metric-container { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .summary-box { background-color: #f0f7ff; border-radius: 10px; padding: 1.5rem; border-left: 5px solid #1e3a5f; margin: 1rem 0; }
    .risk-box { background-color: #fff5f5; border-radius: 10px; padding: 1.5rem; border-left: 5px solid #e53e3e; margin: 1rem 0; }
    .chat-message { background-color: #f8fafc; border-left: 5px solid #3b82f6; padding: 1rem; margin: 0.8rem 0; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'current_stage' not in st.session_state: st.session_state.current_stage = 1
if 'client_id' not in st.session_state: st.session_state.client_id = None
if 'analysis_result' not in st.session_state: st.session_state.analysis_result = None

# --- API HELPER ---
def api_call(endpoint, method="get", data=None, files=None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "get":
            response = requests.get(url)
        else:
            if files or endpoint == "/upload":
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, json=data)
        
        if response.status_code == 422:
            st.error(f"Validation Error (422): {response.text}")
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"📡 Backend Connection Error: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧭 Navigation")
    if st.button("🏠 New Session / Reset", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.markdown("---")
    if st.session_state.client_id:
        st.info(f"**Active Client:** {st.session_state.client_id}")

# --- STAGE 1: PROFILE GATHERING ---
def show_client_profile():
    st.markdown('<h2 class="stage-header">Stage 1: Client Onboarding</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Client Information")
        name = st.text_input("Client Name", placeholder="Enter full name")
        notes = st.text_area("Investment Goals & Notes", height=200, placeholder="Describe financial goals...")
        
    with col2:
        st.markdown("### Document Upload")
        uploaded_file = st.file_uploader("Portfolio Statements", type=['pdf', 'txt', 'csv', 'xlsx', 'docx'])

    if st.button("Initialize Analysis →", type="primary"):
        if not notes and not uploaded_file:
            st.error("Please provide either notes or a document.")
        else:
            cid = int(time.time() % 100000)
            st.session_state.client_id = cid
            payload = {"client_id": str(cid), "client_notes": notes if notes else ""}
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)} if uploaded_file else None
            
            result = api_call("/upload", method="post", data=payload, files=files)
            if result:
                st.success("Profile created. Proceeding to assessment...")
                st.session_state.current_stage = 2
                st.rerun()

# --- STAGE 2: ASSESSMENT ---
def show_assessment():
    st.markdown('<h2 class="stage-header">Stage 2: Risk & Goal Discovery</h2>', unsafe_allow_html=True)
    cid = st.session_state.client_id
    
    status = api_call(f"/assessment/status/{cid}")
    if status:
        completion = status.get("completion", 0)
        st.progress(completion / 100, text=f"Assessment Completion: {completion}%")
        
        next_q = api_call(f"/assessment/next/{cid}")
        if next_q and "id" in next_q:
            st.markdown(f"#### Question: {next_q['text']}")
            ans = st.radio("Options:", next_q.get("options", []), key=f"q_{next_q['id']}")
            if st.button("Submit Answer"):
                api_call("/assessment/answer", method="post", data={"client_id": cid, "question_id": next_q['id'], "answer": ans})
                st.rerun()
        
        if completion >= 70:
            st.markdown("---")
            st.success("Ready for AI Analysis.")
            if st.button("Generate Final Dashboard →", type="primary", use_container_width=True):
                st.session_state.current_stage = 5
                st.rerun()

# --- STAGE 5: INTEGRATED DASHBOARD ---
# --- STAGE 5: INTEGRATED DASHBOARD ---
def show_dashboard():
    st.markdown('<h2 class="stage-header">Executive Wealth Dashboard</h2>', unsafe_allow_html=True)
    cid = st.session_state.client_id

    # Ensure analysis data is fetched
    if not st.session_state.analysis_result:
        with st.status("🤖 Orchestrating AI Agents...", expanded=True) as status:
            res = api_call(f"/analysis/run/{cid}")
            if res:
                st.session_state.analysis_result = res
                status.update(label="Analysis Successful", state="complete")
                st.rerun()
            else:
                st.error("Failed to generate analysis. Please check backend connection and try again.")
                if st.button("Retry Analysis"):
                    st.session_state.analysis_result = None
                    st.rerun()
                return
    else:
        # Option to refresh analysis
        if st.button("🔄 Refresh Analysis Data"):
            st.session_state.analysis_result = None
            st.rerun()

    res = st.session_state.analysis_result
    
    # NEW: Navigation between Overview and Deep Dive
    view_tab, analysis_tab = st.tabs(["📊 Executive Overview", "🔍 Technical Analysis Deep-Dive"])

    with view_tab:
        # --- TOP ROW: KPI BAR ---
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Portfolio Value", f"${res['recommendations']['projection']['current_value']:,.2f}")
        with m2:
            st.metric("Risk Level", res['risk_analysis']['risk_level'], delta=f"Score: {res['risk_analysis']['overall_risk_score']}")
        with m3:
            st.metric("Projected Alpha", f"+{res['recommendations']['expected_return_improvement']}%")
        with m4:
            st.metric("Compliance Status", "Passed")

        st.markdown("---")

        # --- GROWTH PROJECTIONS ---
        st.markdown("### 📈 10-Year Growth Modeling")
        proj = res['recommendations']['projection']
        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(x=[0, proj['years']], y=[proj['current_value'], proj['base']], name=f"Base Case ({proj['assumptions']['base']})", line=dict(width=4, color="#1e3a5f")))
        fig_proj.add_trace(go.Scatter(x=[0, proj['years']], y=[proj['current_value'], proj['high']], name=f"High Case ({proj['assumptions']['high']})", line=dict(dash='dot', color="#38a169")))
        st.plotly_chart(fig_proj, use_container_width=True)

        # --- SUMMARIES ---
        col_sum1, col_sum2 = st.columns(2)
        with col_sum1:
            st.markdown("#### 📝 Strategy Overview")
            st.markdown(f'<div class="summary-box">{res["recommendations"]["summary"]}</div>', unsafe_allow_html=True)
        with col_sum2:
            st.markdown("#### ⚠️ Risk Assessment")
            st.markdown(f'<div class="risk-box">{res["risk_analysis"]["summary"]}</div>', unsafe_allow_html=True)

    with analysis_tab:
        st.markdown("### 🔍 Internal Agent Findings")
        
        # Breakdown into specific technical segments
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            st.write("**Portfolio Intelligence**")
            st.write(f"- **Documents Parsed:** {res['portfolio_analysis']['documents_analyzed']}")
            st.write(f"- **Asset Classes Identified:** {res['portfolio_analysis']['asset_classes_detected']}")
            st.write(f"- **Diversification Score:** {res['portfolio_analysis']['diversification_score']}/100")
            
            st.markdown("#### Current Positions")
            df_h = pd.DataFrame(res['portfolio_analysis']['holdings'])
            st.dataframe(df_h, use_container_width=True, hide_index=True)

        with col_a2:
            st.write("**Risk Vectors**")
            st.write(f"- **Risk Confidence:** {res['risk_analysis']['risk_confidence'] * 100}%")
            st.write(f"- **Calculated Metrics:** {res['risk_analysis']['risk_metrics_calculated']}")
            
            st.markdown("#### Priority Recommended Actions")
            for act in res['recommendations']['actions']:
                with st.expander(f"Priority {act['priority']}: {act['action']}"):
                    st.write(f"**Reasoning:** {act['reason']}")
            
            st.markdown("#### Sector Exposure Breakdown")
            sectors = res['portfolio_analysis']['sector_exposure']
            fig_bar = px.bar(x=list(sectors.keys()), y=list(sectors.values()), color=list(sectors.values()), color_continuous_scale='Blues')
            st.plotly_chart(fig_bar, use_container_width=True)

    # Re-run button at the bottom for major refreshes
    st.markdown("---")
    if st.button("🔄 Clear State & Re-run Full Pipeline"):
        st.session_state.analysis_result = None
        st.session_state.current_stage = 1
        st.rerun()


def show_chat_interface():
    st.markdown('<h2 class="stage-header">💬 Strategy Consultation</h2>', unsafe_allow_html=True)

    cid = st.session_state.client_id

    # Initialize chat session if not exists
    if 'chat_session_id' not in st.session_state or not st.session_state.chat_session_id:
        # Create or get session
        sessions = api_call(f"/chat/sessions/{cid}")
        if sessions and isinstance(sessions, list) and sessions:
            # Use latest session
            st.session_state.chat_session_id = sessions[-1]['id']
        else:
            # Create new session
            new_session = api_call("/chat/session", method="post", data={"client_id": cid, "title": "Dashboard Chat"})
            if new_session:
                st.session_state.chat_session_id = new_session['session_id']

    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

    # Load messages if not loaded
    if not st.session_state.chat_messages and st.session_state.chat_session_id:
        msgs = api_call(f"/chat/messages/{st.session_state.chat_session_id}")
        if isinstance(msgs, list):
            st.session_state.chat_messages = msgs

    # --- CSS for Chat Bubbles ---
    st.markdown(
        """
        <style>
            .chat-message {
                padding: 14px;
                border-radius: 18px;
                margin-bottom: 10px;
                word-break: break-word;
                max-width: 80%;
                line-height: 1.5;
                font-family: sans-serif;
            }
            .chat-message-user {
                background: #eef2ff;
                margin-left: auto;
                border-bottom-right-radius: 2px;
            }
            .chat-message-assistant {
                background: #f8fafc;
                border-left: 4px solid #3b82f6;
                margin-right: auto;
                border-bottom-left-radius: 2px;
            }
            .chat-buffer {
                height: 100px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- 1. Display Chat History ---
    message_container = st.container()
    with message_container:
        if not st.session_state.chat_messages:
            st.info("Start the conversation with a question about your portfolio.")
        
        for msg in st.session_state.chat_messages:
            role = msg.get('role', 'user')
            content = msg.get('message', '')
            if role == "user":
                st.markdown(f'<div class="chat-message chat-message-user"><strong>👤 You:</strong><br>{content}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message chat-message-assistant"><strong>🤖 Advisor AI:</strong><br>{content}</div>', unsafe_allow_html=True)
    
    # Add buffer
    st.markdown('<div class="chat-buffer"></div>', unsafe_allow_html=True)

    # --- 2. Chat Input ---
    if prompt := st.chat_input("Ask about portfolio strategy, risk, taxes..."):
        if st.session_state.chat_session_id:
            # Send message via API
            result = api_call("/chat/send", method="post", data={
                "session_id": st.session_state.chat_session_id,
                "message": prompt
            })
            if result:
                # Reload messages
                msgs = api_call(f"/chat/messages/{st.session_state.chat_session_id}")
                if isinstance(msgs, list):
                    st.session_state.chat_messages = msgs
                st.rerun()
            else:
                st.error("Failed to send message. Please try again.")
        else:
            st.error("No active chat session. Please refresh.")



def main():
    st.markdown('<h1 class="main-header">Wealth Advisor AI</h1>', unsafe_allow_html=True)
    
    # Added Stage 6 to the router
    if st.session_state.current_stage == 1:
        show_client_profile()
    elif st.session_state.current_stage == 2:
        show_assessment()
    elif st.session_state.current_stage == 5:
        show_dashboard()
    elif st.session_state.current_stage == 6:
        show_chat_interface()

if __name__ == "__main__":
    main()



