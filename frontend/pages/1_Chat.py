"""
WealthAdvisorAI - Chat Interface
Dedicated chat interface for conversational interactions with clients
"""

import streamlit as st
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional

# Configuration
API_BASE_URL = "http://localhost:8081/v1"

st.set_page_config(
    page_title="Chat - Wealth Advisor AI",
    layout="wide"
)

st.markdown("""
<style>
    .chat-message-user {
        display: flex;
        justify-content: flex-end;
        margin: 1rem 0;
    }
    .chat-message-assistant {
        display: flex;
        justify-content: flex-start;
        margin: 1rem 0;
    }
    .chat-bubble-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 1rem 1rem 0.25rem 1rem;
        max-width: 70%;
        word-wrap: break-word;
    }
    .chat-bubble-assistant {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        padding: 1rem 1.5rem;
        border-radius: 1rem 1rem 1rem 0.25rem;
        max-width: 70%;
        word-wrap: break-word;
    }
    .chat-meta {
        font-size: 0.75rem;
        color: #718096;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

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
            response = requests.get(url, timeout=10)
        elif method == "post":
            response = requests.post(url, json=data, timeout=10)
        elif method == "delete":
            response = requests.delete(url, timeout=10)
        else:
            return None
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

with st.sidebar:
    st.title("Chat Sessions")
    
    client_id_val = st.number_input(
        "Client ID",
        min_value=1,
        value=int(st.session_state.client_id) if st.session_state.client_id else 1,
        key="sidebar_client_id"
    )
    st.session_state.client_id = client_id_val
    
    st.divider()
    
    if st.button("Refresh Sessions", use_container_width=True):
        st.rerun()
    
    sessions_data = api_call(f"/chat/sessions/{client_id_val}")
    sessions: List[Dict[str, Any]] = sessions_data if isinstance(sessions_data, list) else []
    
    if sessions:
        for session in sessions:
            col1, col2 = st.columns([3, 1])
            with col1:
                session_name = session.get('title', 'Untitled')
                if st.button(
                    f"Session: {session_name}",
                    key=f"session_{session.get('id')}",
                    use_container_width=True
                ):
                    st.session_state.chat_session_id = session.get('id')
                    st.session_state.messages = []
                    st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_{session.get('id')}"):
                    api_call(f"/chat/session/{session.get('id')}", method="delete")
                    st.rerun()
    
    st.divider()
    
    with st.expander("New Session"):
        session_title = st.text_input("Session Title", placeholder="e.g., Portfolio Review")
        if st.button("Create Session", use_container_width=True):
            new_session = api_call("/chat/session", method="post", data={
                "client_id": client_id_val,
                "title": session_title or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            })
            if new_session and isinstance(new_session, dict):
                st.session_state.chat_session_id = new_session.get('session_id')
                st.session_state.messages = []
                st.success("Session created")
                st.rerun()

st.title("Client Chat")

if not st.session_state.chat_session_id:
    st.info("Select an existing session from the sidebar or create a new one to start.")
    
    if st.button("Quick Start - Create Session"):
        quick_session = api_call("/chat/session", method="post", data={
            "client_id": st.session_state.client_id,
            "title": f"Quick Chat {datetime.now().strftime('%H:%M')}"
        })
        if quick_session and isinstance(quick_session, dict):
            st.session_state.chat_session_id = quick_session.get('session_id')
            st.session_state.messages = []
            st.rerun()
else:
    session_info_data = api_call(f"/chat/session/{st.session_state.chat_session_id}")
    if session_info_data and isinstance(session_info_data, dict):
        st.caption(f"Session: {session_info_data.get('title', 'Untitled')} | Client: {session_info_data.get('client_id')}")
    
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            msg_data = api_call(f"/chat/messages/{st.session_state.chat_session_id}")
            if isinstance(msg_data, list):
                st.session_state.messages = msg_data
        
        for msg in st.session_state.messages:
            role = msg.get('role', 'user')
            content = msg.get('message', '')
            timestamp = msg.get('created_at', '')
            
            if role == 'user':
                st.markdown(f"""
                <div class="chat-message-user">
                    <div class="chat-bubble-user">
                        {content}
                        <div class="chat-meta">{timestamp}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message-assistant">
                    <div class="chat-bubble-assistant">
                        <strong>Advisor AI:</strong><br><br>
                        {content}
                        <div class="chat-meta">{timestamp}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "Your message:",
            placeholder="Type your message here...",
            key="chat_input_box"
        )
    with col2:
        if st.button("Send", type="primary", use_container_width=True):
            if user_input and st.session_state.chat_session_id:
                send_result = api_call("/chat/send", method="post", data={
                    "session_id": st.session_state.chat_session_id,
                    "message": user_input
                })
                
                if send_result:
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error("Failed to send message")

st.markdown("---")
st.caption("Tip: Use the chat to discuss portfolio strategies, ask questions about recommendations, or get clarification on analysis results.")