"""
AI Finance Agent - Frontend Application

This is a minimal Streamlit frontend for:
- Chat interface
- CSV portfolio upload
- Displaying results

IMPORTANT: This frontend is intentionally DUMB.
All business logic lives in the backend.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add Backend to path so we can import (for local dev)
backend_path = Path(__file__).parent.parent / "Backend"
sys.path.insert(0, str(backend_path))


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="AI Finance Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "uploaded_portfolio" not in st.session_state:
        st.session_state.uploaded_portfolio = None
    
    if "portfolio_df" not in st.session_state:
        st.session_state.portfolio_df = None


initialize_session_state()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def add_message(role: str, content: str):
    """Add a message to chat history."""
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })


def parse_portfolio_csv(uploaded_file) -> pd.DataFrame:
    """
    Parse uploaded CSV portfolio.
    
    Expected format:
    ticker,quantity
    AAPL,10
    MSFT,5
    
    Returns:
        DataFrame with portfolio data
    """
    try:
        df = pd.read_csv(uploaded_file)
        
        # Basic validation - check for required columns
        required_cols = ["ticker", "quantity"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"CSV must contain columns: {required_cols}")
            return None
        
        return df
    
    except Exception as e:
        st.error(f"Error parsing CSV: {e}")
        return None


def send_to_backend_stub(message: str, portfolio_data=None) -> str:
    """
    Stub function for backend communication.
    
    For Day 7: Just returns dummy response.
    Later: Will call actual backend API.
    
    Args:
        message: User's chat message
        portfolio_data: Portfolio DataFrame if uploaded
        
    Returns:
        Backend response (stub)
    """
    # TODO Day 8: Replace with actual backend API call
    
    if portfolio_data is not None:
        portfolio_summary = f"\n- Portfolio uploaded: {len(portfolio_data)} positions"
    else:
        portfolio_summary = ""
    
    return f"""Backend Response (Stub)

Message received: "{message}"{portfolio_summary}

Frontend to Backend connection working.
Real analysis coming in Day 8+.
"""


# ============================================================================
# MAIN UI
# ============================================================================

def main():
    """Main application UI."""
    
    st.title("AI Finance Agent")
    st.markdown("---")
    
    with st.sidebar:
        st.header("Portfolio Upload")
        
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=["csv"],
            help="Upload portfolio in ticker,quantity format"
        )
        
        if uploaded_file is not None:
            df = parse_portfolio_csv(uploaded_file)
            
            if df is not None:
                st.session_state.uploaded_portfolio = uploaded_file.name
                st.session_state.portfolio_df = df
                
                st.success(f"Uploaded: {uploaded_file.name}")
                
                st.subheader("Preview")
                st.dataframe(df, use_container_width=True)
                
                st.metric("Total Positions", len(df))
                st.metric("Total Quantity", df["quantity"].sum())
        
        if st.session_state.uploaded_portfolio is not None:
            if st.button("Clear Portfolio"):
                st.session_state.uploaded_portfolio = None
                st.session_state.portfolio_df = None
                st.rerun()
    
    # Chat Interface - Full Width
    chat_container = st.container(height=500)
    
    with chat_container:
        if len(st.session_state.messages) == 0:
            st.markdown("Welcome. Ask about your portfolio or financial data.")
        else:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    st.caption(f"{msg['timestamp']}")
    
    user_input = st.chat_input("Type your message...")
    
    if user_input:
        add_message("user", user_input)
        
        response = send_to_backend_stub(
            user_input,
            st.session_state.portfolio_df
        )
        
        add_message("assistant", response)
        st.rerun()


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()
