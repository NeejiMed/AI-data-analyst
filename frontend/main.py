"""
AI Data Analyst - Streamlit Frontend
Main application entry point for the Streamlit interface.
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st  # noqa: E402

from frontend.components import (
    render_charts,
    render_chat_message,
    render_header,
    render_insights,
    render_recommendations,
    render_report_download,
    render_sidebar,
    render_sql_result,
)
from frontend.styles import CUSTOM_CSS  # noqa: E402

# Page configuration
st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Session state initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "db" not in st.session_state:
    from app.data.database import SessionLocal  # noqa: E402
    st.session_state.db = SessionLocal()
if "workflow" not in st.session_state:
    from app.agents.workflow import AnalyticsWorkflow  # noqa: E402
    st.session_state.workflow = AnalyticsWorkflow(st.session_state.db)

# Layout
render_header()
render_sidebar()

# Chat input
question = st.chat_input("Ask a business question...")

# Handle sidebar example question clicks
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None

# Process user question
if question:
    # Add to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": question
    })

    # Run the analytics workflow
    with st.spinner("Analyzing your question..."):
        response = st.session_state.workflow.run(question)
        response_dict = response.to_dict() # Convert to dict for easier handling
        st.session_state.last_response = response_dict # Store the last response for rendering

    # Add response to chat history
    summary = response_dict.get("executive_summary", "")
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": summary[:500] + "..." if len(summary) > 500 else summary
    })

# Chat history display
if st.session_state.chat_history:
    st.markdown("### Conversation")
    for message in st.session_state.chat_history:
        render_chat_message(message["role"], message["content"])
    st.markdown("")

# Results display
response = st.session_state.last_response

if response and response.get("success"):
    st.divider()

    intent = response.get("intent", "")
    processing_ms = response.get("processing_time_ms", 0)

    col1, col2, col3 = st.columns(3) # For intent, processing time, and report download link
    with col1:
        st.markdown(f"Intent: `{intent}`")
    with col2:
        st.markdown(f"Processing Time: `{processing_ms}ms`")
    with col3:
        render_report_download(response.get("report_paths", {}))

    # Tabs for different result sections
    tab_labels = ["Summary", "Insights", "Charts", "Data", "Actions"]
    tabs = st.tabs(tab_labels) # Create tabs for different sections of the response

    with tabs[0]: # Summary tab
        st.markdown("### Executive Summary")
        st.markdown(response.get("executive_summary", ""))

        if response.get("positive_signals"):
            st.markdown("**Positive signals**")
            for signal in response["positive_signals"]:
                st.markdown(f"- ✅ {signal}")

        if response.get("risk_factors"):
            st.markdown("**Risk factors**")
            for risk in response["risk_factors"]:
                st.markdown(f"- ⚠️ {risk}")

    with tabs[1]: # Insights tab
        render_insights(response.get("insights", []))

    with tabs[2]: # Charts tab
        render_charts(response.get("chart_paths", {}))

    with tabs[3]: # Data tab
        render_sql_result(response)

        if not response.get("sql_query"):
            st.info(
                "This analysis used the pre-computed analytics engine. "
                "Ask a specific data question to see SQL results."
            )

    with tabs[4]: # Actions tab
        render_recommendations(response.get("recommended_actions", []))

elif response and not response.get("success"):
    st.error(f"Analysis failed: {response.get('error', 'Unknown error')}")

elif not st.session_state.chat_history:
    # Welcome screen
    st.markdown("### Welcome to AI Data Analyst")
    st.markdown(
        "Ask any business question in plain English. "
        "The AI will analyze your data, generate insights, "
        "create charts, and produce a downloadable report."
    )

    st.markdown("**Try asking:**")
    cols = st.columns(2)
    examples = [
        "Analyze monthly sales trends and explain anomalies",
        "Generate customer segmentation insights",
        "Why did revenue decrease in Q2?",
        "What is the total revenue by product category?"
    ]
    for i, example in enumerate(examples):
        with cols[i % 2]:
            st.markdown(f"- *{example}*")
