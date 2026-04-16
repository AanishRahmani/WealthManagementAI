
"""
WealthAdvisorAI - Chat Interface
Dedicated chat interface for conversational interactions with clients
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional
import time

# Configuration
API_BASE_URL = "http://localhost:8081/v1"

st.set_page_config(
    page_title="Chat - Wealth Advisor AI",
    page_icon="💬",
    layout="wide"
)

# --- OMNI-THEME AWARENESS ---
try:
    theme_type = st.context.theme.type
except Exception:
    theme_type = "light"

# Inject tailored palettes instead of system defaults for higher quality UI
if theme_type == "dark":
    user_bubble_bg = "#334155"
    user_bubble_text = "white"
    assistant_bubble_bg = "#0f172a"
    assistant_bubble_text = "#e2e8f0"
    assistant_meta = "#64748b"
else:
    user_bubble_bg = "#1e3a5f"
    user_bubble_text = "white"
    assistant_bubble_bg = "#f1f5f9"
    assistant_bubble_text = "#1e293b"
    assistant_meta = "#94a3b8"

# --- MODERNIZED UI STYLING ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* Padding for the bottom so input doesn't overlap last message */
    .main .block-container {{
        padding-bottom: 120px;
    }}

    .chat-message-user {{
        display: flex;
        justify-content: flex-end;
        margin: 0.8rem 0;
    }}
    .chat-message-assistant {{
        display: flex;
        justify-content: flex-start;
        margin: 0.8rem 0;
    }}
    .chat-bubble-user {{
        background: {user_bubble_bg};
        color: {user_bubble_text};
        padding: 0.8rem 1.2rem;
        border-radius: 12px 12px 2px 12px;
        max-width: 75%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    .chat-bubble-assistant {{
        background-color: {assistant_bubble_bg};
        color: {assistant_bubble_text};
        border-left: 4px solid #3b82f6;
        padding: 0.8rem 1.2rem;
        border-radius: 12px 12px 12px 2px;
        max-width: 75%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }}
    .chat-meta {{
        font-size: 0.7rem;
        color: {assistant_meta};
        margin-top: 0.4rem;
        text-align: right;
    }}
    .assistant-name {{
        font-weight: 600;
        color: #3b82f6;
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
    }}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE & API HELPERS (Preserved Logic) ---
if 'chat_session_id' not in st.session_state:
    st.session_state.chat_session_id = None
if 'client_id' not in st.session_state:
    st.session_state.client_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

def api_call(endpoint: str, method: str = "get", data: Optional[Dict[str, Any]] = None) -> Any:
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "get":
            response = requests.get(url, timeout=90)
        elif method == "post":
            response = requests.post(url, json=data, timeout=90)
        elif method == "delete":
            response = requests.delete(url, timeout=90)
        else:
            return None
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# --- SIDEBAR: SESSION MANAGEMENT ---
with st.sidebar:
    st.markdown("### 🏦 Client Context")
    client_id_val = st.number_input(
        "Active Client ID",
        min_value=1,
        value=int(st.session_state.client_id) if st.session_state.client_id else 1,
        key="sidebar_client_id"
    )
    st.session_state.client_id = client_id_val
    
    st.markdown("---")
    st.markdown("### 💬 Chat History")
    
    sessions_data = api_call(f"/chat/sessions/{client_id_val}")
    sessions: List[Dict[str, Any]] = sessions_data if isinstance(sessions_data, list) else []
    
    if sessions:
        for session in sessions:
            col_s, col_d = st.columns([4, 1])
            with col_s:
                is_active = "🔵" if st.session_state.chat_session_id == session.get('id') else ""
                if st.button(f"{is_active} {session.get('title', 'Untitled')}", key=f"s_{session.get('id')}", use_container_width=True):
                    st.session_state.chat_session_id = session.get('id')
                    st.session_state.messages = []
                    st.rerun()
            with col_d:
                if st.button("🗑️", key=f"del_{session.get('id')}", help="Delete Session"):
                    api_call(f"/chat/session/{session.get('id')}", method="delete")
                    st.rerun()
    else:
        st.caption("No recent sessions found.")

    st.markdown("---")
    with st.expander("➕ Start New Consultation"):
        session_title = st.text_input("Consultation Topic")
        if st.button("Create New Chat", use_container_width=True, type="primary"):
            new_session = api_call("/chat/session", method="post", data={
                "client_id": client_id_val,
                "title": session_title or f"Consultation {datetime.now().strftime('%H:%M')}"
            })
            if new_session:
                st.session_state.chat_session_id = new_session.get('session_id')
                st.session_state.messages = []
                st.rerun()

# --- MAIN CHAT INTERFACE ---
st.markdown('<h2 style="color:#1e3a5f; margin-bottom:0;">Strategy Consultation</h2>', unsafe_allow_html=True)

if not st.session_state.chat_session_id:
    st.info("Select a session from the sidebar or create a new one to begin your strategy review.")
    if st.button("🚀 Quick Start New Session"):
        quick_session = api_call("/chat/session", method="post", data={
            "client_id": st.session_state.client_id,
            "title": f"Quick Review {datetime.now().strftime('%H:%M')}"
        })
        if quick_session:
            st.session_state.chat_session_id = quick_session.get('session_id')
            st.session_state.messages = []
            st.rerun()
else:
    # Session Header
    session_info = api_call(f"/chat/session/{st.session_state.chat_session_id}")
    if session_info:
        st.caption(f"Topic: **{session_info.get('title')}** | Client ID: {st.session_state.client_id}")
    
    # Message Display Container
    message_container = st.container()
    
    with message_container:
        if not st.session_state.messages:
            msg_data = api_call(f"/chat/messages/{st.session_state.chat_session_id}")
            if isinstance(msg_data, list):
                st.session_state.messages = msg_data
        
        for msg in st.session_state.messages:
            role = msg.get('role', 'user')
            content = msg.get('message', '')
            # Simple timestamp formatting if needed
            ts = msg.get('created_at', '')[:16].replace('T', ' ') 
            
            if role == 'user':
                st.markdown(f"""
                <div class="chat-message-user">
                    <div class="chat-bubble-user">
                        {content}
                        <div class="chat-meta" style="color:#cbd5e1">{ts}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message-assistant">
                    <div class="chat-bubble-assistant">
                        <div class="assistant-name">Advisor AI</div>
                        {content}
                        <div class="chat-meta">{ts}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- THE FIXED UI FIX: Unified Chat Input ---
    # This replaces the messy columns with a modern pinned input bar
    if prompt := st.chat_input("Ask about your portfolio or strategy..."):
        # 1. Update UI immediately for User
        st.session_state.messages.append({"role": "user", "message": prompt, "created_at": "Just now"})
        
        # 2. Call API
        with st.spinner("Analyzing..."):
            send_result = api_call("/chat/send", method="post", data={
                "session_id": st.session_state.chat_session_id,
                "message": prompt
            })
            
            if send_result:
                # Refresh messages from server to get AI response
                st.session_state.messages = [] 
                st.rerun()
            else:
                st.error("Connection lost. Please try again.")

# Footer Tip
st.markdown("""
<div style="position: fixed; bottom: 70px; left: 20rem; right: 2rem; text-align: center; opacity: 0.5; font-size: 0.8rem;">
    Wealth Advisor AI can discuss tax implications, sector risks, and rebalancing needs.
</div>
""", unsafe_allow_html=True)