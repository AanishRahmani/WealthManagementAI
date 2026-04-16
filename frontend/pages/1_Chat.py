# """
# WealthAdvisorAI - Chat Interface
# Dedicated chat interface for conversational interactions with clients
# """

# import streamlit as st
# import requests
# from datetime import datetime
# from typing import Any, Dict, List, Optional

# # Configuration
# API_BASE_URL = "http://localhost:8081/v1"

# st.set_page_config(
#     page_title="Chat - Wealth Advisor AI",
#     layout="wide"
# )

# st.markdown("""
# <style>
#     .chat-message-user {
#         display: flex;
#         justify-content: flex-end;
#         margin: 1rem 0;
#     }
#     .chat-message-assistant {
#         display: flex;
#         justify-content: flex-start;
#         margin: 1rem 0;
#     }
#     .chat-bubble-user {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         color: white;
#         padding: 1rem 1.5rem;
#         border-radius: 1rem 1rem 0.25rem 1rem;
#         max-width: 70%;
#         word-wrap: break-word;
#     }
#     .chat-bubble-assistant {
#         background-color: #f7fafc;
#         border: 1px solid #e2e8f0;
#         padding: 1rem 1.5rem;
#         border-radius: 1rem 1rem 1rem 0.25rem;
#         max-width: 70%;
#         word-wrap: break-word;
#     }
#     .chat-meta {
#         font-size: 0.75rem;
#         color: #718096;
#         margin-top: 0.5rem;
#     }
# </style>
# """, unsafe_allow_html=True)

# if 'chat_session_id' not in st.session_state:
#     st.session_state.chat_session_id = None
# if 'client_id' not in st.session_state:
#     st.session_state.client_id = None
# if 'messages' not in st.session_state:
#     st.session_state.messages = []

# def api_call(endpoint: str, method: str = "get", data: Optional[Dict[str, Any]] = None) -> Any:
#     try:
#         url = f"{API_BASE_URL}{endpoint}"
#         if method == "get":
#             response = requests.get(url, timeout=10)
#         elif method == "post":
#             response = requests.post(url, json=data, timeout=10)
#         elif method == "delete":
#             response = requests.delete(url, timeout=10)
#         else:
#             return None
        
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         st.error(f"API Error: {e}")
#         return None

# with st.sidebar:
#     st.title("Chat Sessions")
    
#     client_id_val = st.number_input(
#         "Client ID",
#         min_value=1,
#         value=int(st.session_state.client_id) if st.session_state.client_id else 1,
#         key="sidebar_client_id"
#     )
#     st.session_state.client_id = client_id_val
    
#     st.divider()
    
#     if st.button("Refresh Sessions", use_container_width=True):
#         st.rerun()
    
#     sessions_data = api_call(f"/chat/sessions/{client_id_val}")
#     sessions: List[Dict[str, Any]] = sessions_data if isinstance(sessions_data, list) else []
    
#     if sessions:
#         for session in sessions:
#             col1, col2 = st.columns([3, 1])
#             with col1:
#                 session_name = session.get('title', 'Untitled')
#                 if st.button(
#                     f"Session: {session_name}",
#                     key=f"session_{session.get('id')}",
#                     use_container_width=True
#                 ):
#                     st.session_state.chat_session_id = session.get('id')
#                     st.session_state.messages = []
#                     st.rerun()
#             with col2:
#                 if st.button("Delete", key=f"delete_{session.get('id')}"):
#                     api_call(f"/chat/session/{session.get('id')}", method="delete")
#                     st.rerun()
    
#     st.divider()
    
#     with st.expander("New Session"):
#         session_title = st.text_input("Session Title", placeholder="e.g., Portfolio Review")
#         if st.button("Create Session", use_container_width=True):
#             new_session = api_call("/chat/session", method="post", data={
#                 "client_id": client_id_val,
#                 "title": session_title or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
#             })
#             if new_session and isinstance(new_session, dict):
#                 st.session_state.chat_session_id = new_session.get('session_id')
#                 st.session_state.messages = []
#                 st.success("Session created")
#                 st.rerun()

# st.title("Client Chat")

# if not st.session_state.chat_session_id:
#     st.info("Select an existing session from the sidebar or create a new one to start.")
    
#     if st.button("Quick Start - Create Session"):
#         quick_session = api_call("/chat/session", method="post", data={
#             "client_id": st.session_state.client_id,
#             "title": f"Quick Chat {datetime.now().strftime('%H:%M')}"
#         })
#         if quick_session and isinstance(quick_session, dict):
#             st.session_state.chat_session_id = quick_session.get('session_id')
#             st.session_state.messages = []
#             st.rerun()
# else:
#     session_info_data = api_call(f"/chat/session/{st.session_state.chat_session_id}")
#     if session_info_data and isinstance(session_info_data, dict):
#         st.caption(f"Session: {session_info_data.get('title', 'Untitled')} | Client: {session_info_data.get('client_id')}")
    
#     chat_container = st.container()
#     with chat_container:
#         if not st.session_state.messages:
#             msg_data = api_call(f"/chat/messages/{st.session_state.chat_session_id}")
#             if isinstance(msg_data, list):
#                 st.session_state.messages = msg_data
        
#         for msg in st.session_state.messages:
#             role = msg.get('role', 'user')
#             content = msg.get('message', '')
#             timestamp = msg.get('created_at', '')
            
#             if role == 'user':
#                 st.markdown(f"""
#                 <div class="chat-message-user">
#                     <div class="chat-bubble-user">
#                         {content}
#                         <div class="chat-meta">{timestamp}</div>
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)
#             else:
#                 st.markdown(f"""
#                 <div class="chat-message-assistant">
#                     <div class="chat-bubble-assistant">
#                         <strong>Advisor AI:</strong><br><br>
#                         {content}
#                         <div class="chat-meta">{timestamp}</div>
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)
    
#     st.divider()
#     col1, col2 = st.columns([5, 1])
#     with col1:
#         user_input = st.text_input(
#             "Your message:",
#             placeholder="Type your message here...",
#             key="chat_input_box"
#         )
#     with col2:
#         if st.button("Send", type="primary", use_container_width=True):
#             if user_input and st.session_state.chat_session_id:
#                 send_result = api_call("/chat/send", method="post", data={
#                     "session_id": st.session_state.chat_session_id,
#                     "message": user_input
#                 })
                
#                 if send_result:
#                     st.session_state.messages = []
#                     st.rerun()
#                 else:
#                     st.error("Failed to send message")

# st.markdown("---")
# st.caption("Tip: Use the chat to discuss portfolio strategies, ask questions about recommendations, or get clarification on analysis results.")


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

# --- MODERNIZED UI STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Padding for the bottom so input doesn't overlap last message */
    .main .block-container {
        padding-bottom: 120px;
    }

    .chat-message-user {
        display: flex;
        justify-content: flex-end;
        margin: 0.8rem 0;
    }
    .chat-message-assistant {
        display: flex;
        justify-content: flex-start;
        margin: 0.8rem 0;
    }
    .chat-bubble-user {
        background: #1e3a5f;
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 12px 12px 2px 12px;
        max-width: 75%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .chat-bubble-assistant {
        background-color: #f1f5f9;
        color: #1e293b;
        border-left: 4px solid #3b82f6;
        padding: 0.8rem 1.2rem;
        border-radius: 12px 12px 12px 2px;
        max-width: 75%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .chat-meta {
        font-size: 0.7rem;
        color: #94a3b8;
        margin-top: 0.4rem;
        text-align: right;
    }
    .assistant-name {
        font-weight: 600;
        color: #3b82f6;
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
    }

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