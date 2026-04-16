
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
if 'analysis_started' not in st.session_state: st.session_state.analysis_started = False

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
            client_payload = {}
            if name:
                client_payload["full_name"] = name
            if notes:
                client_payload["goals"] = notes

            client_result = api_call("/clients", method="post", data=client_payload)
            if not client_result:
                st.error("Failed to create client.")
                return

            cid = client_result.get("client_id")
            if cid is None:
                st.error("Client creation failed: missing client_id.")
                return

            st.session_state.client_id = cid

            upload_payload = {
                "client_id": str(cid),
                "client_full_name": name if name else None,
                "client_goals": notes if notes else None,
                "client_notes": notes if notes else None,
            }
            upload_files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)} if uploaded_file else None

            upload_result = api_call("/upload", method="post", data=upload_payload, files=upload_files)
            if upload_result:
                st.success("Profile created. Proceeding to assessment...")
                st.session_state.current_stage = 2
                st.rerun()
            else:
                st.error("Failed to upload client documents.")

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
            if st.button("Generate AI Analysis →", type="primary", use_container_width=True):
                st.session_state.current_stage = 3
                st.session_state.analysis_started = False
                st.session_state.analysis_result = None
                st.rerun()

# --- STAGE 3: AI ANALYSIS ---
def show_analysis_stage():
    st.markdown('<h2 class="stage-header">Stage 3: AI-Powered Analysis</h2>', unsafe_allow_html=True)
    cid = st.session_state.client_id

    if not st.session_state.analysis_started:
        st.info("Start the three-agent AI analysis pipeline. This will simulate progress and then execute the backend analysis.")
        if st.button("Start AI Analysis", type="primary", use_container_width=True):
            st.session_state.analysis_started = True
            st.session_state.analysis_result = None
            st.rerun()
        return

    progress_bar = st.progress(0)
    status1 = st.empty()
    status2 = st.empty()
    status3 = st.empty()
    stage_message = st.empty()

    status1.info("Portfolio Analysis Agent: queued")
    status2.info("Risk Assessment Agent: waiting")
    status3.info("Recommendation Agent: waiting")
    stage_message.info("Preparing agent pipeline...")
    time.sleep(0.5)
    progress_bar.progress(10)

    status1.success("Portfolio Analysis Agent: running")
    stage_message.info("Analyzing client documents and portfolio exposure...")
    time.sleep(1.0)
    progress_bar.progress(30)

    status2.info("Risk Assessment Agent: queued")
    time.sleep(0.4)
    progress_bar.progress(40)

    status2.success("Risk Assessment Agent: running")
    stage_message.info("Assessing concentration, liquidity, and compliance risks...")
    time.sleep(1.0)
    progress_bar.progress(55)

    status3.info("Recommendation Agent: queued")
    time.sleep(0.4)
    progress_bar.progress(65)

    status3.success("Recommendation Agent: running")
    stage_message.info("Synthesizing recommendations, projections, and scenario outputs...")
    time.sleep(1.0)
    progress_bar.progress(80)

    stage_message.info("Finalizing results...")
    time.sleep(0.8)
    progress_bar.progress(90)

    analysis_result = api_call(f"/analysis/run/{cid}")
    if analysis_result:
        st.session_state.analysis_result = analysis_result
        st.session_state.analysis_started = False
        st.session_state.current_stage = 4
        st.rerun()
    else:
        stage_message.error("Analysis failed. Please retry.")
        st.session_state.analysis_started = False
        if st.button("Retry Analysis", use_container_width=True):
            st.rerun()


def show_recommendation_scoring():
    st.markdown('<h2 class="stage-header">Stage 4: Recommendation Scoring & Decision</h2>', unsafe_allow_html=True)
    cid = st.session_state.client_id

    report = api_call(f"/dashboard/client/{cid}")
    if not report:
        st.error("Failed to load scoring data.")
        return

    feasibility_label = report.get("feasibility_label", "N/A")
    impact_label = report.get("impact_label", "N/A")
    feasibility_color = "#16a34a" if feasibility_label == "Green" else "#f59e0b" if feasibility_label == "Amber" else "#ef4444"
    impact_color = "#16a34a" if impact_label == "Green" else "#f59e0b" if impact_label == "Amber" else "#ef4444"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Feasibility Score")
        st.markdown(f"<div style='font-size:1.8rem;font-weight:700'>{report.get('feasibility_score', 0):.0f}</div>")
        st.markdown(build_badge(feasibility_label, feasibility_color), unsafe_allow_html=True)
        st.write("Implementation complexity, cost, and liquidity readiness.")
    with col2:
        st.markdown("#### Impact Score")
        st.markdown(f"<div style='font-size:1.8rem;font-weight:700'>{report.get('impact_score', 0):.0f}</div>")
        st.markdown(build_badge(impact_label, impact_color), unsafe_allow_html=True)
        st.write("Expected portfolio improvement and goal alignment.")

    st.markdown("---")
    stats = st.columns(4)
    stats[0].metric("Projected Annual Return", f"+{report.get('projected_annual_return', 0):.2f}%")
    stats[1].metric("3Y Portfolio Value", f"${report.get('projected_value_3y', 0):,.2f}")
    stats[2].metric("Implementation Cost", f"${report.get('implementation_cost', 0):,.0f}")
    stats[3].metric("Tax Implications", f"${report.get('tax_implications', 0):,.2f}")

    st.markdown("---")
    st.markdown("### Agent Findings")
    findings = report.get("agent_findings", {})

    with st.expander("Portfolio Analysis Findings"):
        portfolio_findings = findings.get("portfolio", {})
        st.write(f"- Holdings identified: {portfolio_findings.get('holdings_identified', 0)}")
        st.write(f"- Asset classes detected: {portfolio_findings.get('asset_classes_detected', 0)}")
        st.write(f"- Diversification score: {portfolio_findings.get('diversification_score', 0)}/100")

    with st.expander("Risk Assessment Findings"):
        risk_findings = findings.get("risk", {})
        st.write(f"- Risk score: {risk_findings.get('overall_risk_score', 0)}")
        st.write(f"- Issues detected: {len(risk_findings.get('issues', []))}")
        st.write(f"- Confidence: {risk_findings.get('risk_confidence', 0) * 100:.0f}%")

    with st.expander("Recommendation Summary"):
        recommendations = findings.get("recommendations", {})
        st.write(f"- Expected return improvement: {recommendations.get('expected_return_improvement', 0)}%")
        st.write(f"- Tax efficiency gain: {recommendations.get('tax_efficiency_gain', 0)}%")
        st.write(f"- Recommendation confidence: {recommendations.get('recommendation_confidence', 0) * 100:.0f}%")
        st.write(f"- Recommendations generated: {recommendations.get('recommendations_generated', 0)}")

    st.markdown("---")
    if st.button("Continue to Portfolio Dashboard →", type="primary", use_container_width=True):
        st.session_state.current_stage = 5
        st.rerun()


def show_portfolio_dashboard():
    st.markdown('<h2 class="stage-header">Stage 5: Portfolio Dashboard</h2>', unsafe_allow_html=True)
    cid = st.session_state.client_id

    client_report = api_call(f"/dashboard/client/{cid}")
    all_reports = api_call("/dashboard/all") or []

    overview_cols = st.columns(3)
    overview_cols[0].metric("Current Decision", client_report.get("decision", "N/A"))
    overview_cols[1].metric("Feasibility", f"{client_report.get('feasibility_score', 0):.0f}")
    overview_cols[2].metric("Impact", f"{client_report.get('impact_score', 0):.0f}")

    st.markdown("---")
    export_col1, export_col2 = st.columns([1, 1])
    if client_report:
        client_json = json.dumps(client_report, indent=2).encode("utf-8")
        export_col1.download_button(
            "Export Current Client JSON",
            data=client_json,
            file_name=f"client_{cid}_dashboard.json",
            mime="application/json",
        )

    if all_reports:
        df = pd.DataFrame(all_reports)
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        export_col2.download_button(
            "Export Portfolio Table CSV",
            data=csv_bytes,
            file_name="portfolio_recommendations.csv",
            mime="text/csv",
        )

    st.markdown("---")
    st.markdown("### Client Recommendations Table")
    if all_reports:
        df_display = pd.DataFrame(all_reports).rename(columns={
            'projected_annual_return': 'Projected Return',
            'implementation_cost': 'Cost',
            'risk_score': 'Risk Score',
        })
        st.dataframe(df_display, use_container_width=True)

        for row in all_reports:
            with st.expander(f"Client {row['client_id']} — {row['decision']} | F {row['feasibility_score']:.0f} | I {row['impact_score']:.0f}"):
                st.write(row)
    else:
        st.info("No client analysis reports found yet.")

    st.markdown("---")
    st.markdown("### Feasibility-Impact Matrix")
    scatter_df = pd.DataFrame(all_reports)
    if not scatter_df.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=scatter_df['feasibility_score'],
                y=scatter_df['impact_score'],
                mode='markers',
                marker=dict(
                    size=14,
                    color='#4c6ef5',
                    line=dict(color='white', width=1),
                    opacity=0.9,
                ),
                text=scatter_df['label'],
                hovertemplate='%{text}<br>Feasibility: %{x}<br>Impact: %{y}<extra></extra>',
            )
        )
        fig.update_layout(
            template='plotly',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title='Feasibility Score', range=[0, 100], gridcolor='rgba(0,0,0,0.08)'),
            yaxis=dict(title='Impact Score', range=[0, 100], gridcolor='rgba(0,0,0,0.08)'),
            shapes=[
                dict(type='line', x0=50, x1=50, y0=0, y1=100, line=dict(color='#94a3b8', width=1, dash='dash')),
                dict(type='line', x0=0, x1=100, y0=50, y1=50, line=dict(color='#94a3b8', width=1, dash='dash')),
            ],
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No scoring data available to build the matrix yet.")

    st.markdown("---")
    if st.button("Continue to Chat Review", use_container_width=True):
        st.session_state.current_stage = 6
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
    
    if st.session_state.current_stage == 1:
        show_client_profile()
    elif st.session_state.current_stage == 2:
        show_assessment()
    elif st.session_state.current_stage == 3:
        show_analysis_stage()
    elif st.session_state.current_stage == 4:
        show_recommendation_scoring()
    elif st.session_state.current_stage == 5:
        show_portfolio_dashboard()
    elif st.session_state.current_stage == 6:
        show_chat_interface()

if __name__ == "__main__":
    main()



