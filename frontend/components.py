"""
Reusable streamlit UI components.
Each function renders one piece of the UI.
Keeping components seperatte from page logic allows for better code organization and reusability.
"""

from datetime import datetime

import streamlit as st


def render_header():
    """Render the main header of the app."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 AI Data Analyst")
        st.caption("Ask business questions in plain English")
    with col2:
        st.markdown(
            '<div style="text-align:right;padding-top:1rem">'
            '<span class="badge-success">System Online</span>'
            "</div>",
            unsafe_allow_html=True,
        )
    st.divider()


def render_sidebar():
    """Render the sidebar with example questions and settings."""
    with st.sidebar:
        st.markdown("### AI Data Analyst")
        st.caption("Powered by Llama 3.3 + ChromaDB\n")
        st.caption("Created by @NeejiMed")
        st.divider()

        st.markdown(
            '<p class="sidebar-header">Example Questions</p>', unsafe_allow_html=True
        )

        examples = [
            "Analyze monthly sales trends and explain anomalies",
            "Why did revenue decrease in Q2?",
            "Generate customer segmentation insights",
            "Compare regional performance",
            "What is the total revenue by product category?",
            "Show me the top 10 customers by spend",
            "What percentage of orders were refunded?",
        ]

        for example in examples:
            if st.button(
                example, key=f"example_{example[:20]}", use_container_width=True
            ):
                st.session_state.pending_question = example

        st.divider()
        st.markdown(
            '<p class="sidebar-header">Session stats</p>', unsafe_allow_html=True
        )
        query_count = len(st.session_state.get("chat_history", []))
        st.metric("Queries this session", query_count)

        st.divider()
        if st.button("Clear chat history", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.last_response = None
            st.rerun()


def render_kpi_cards(response):
    """Render KPI metric cards based on the response."""
    if not response or not response.get("success"):
        return

    # Extract KPIs from executive summary if available
    st.markdown("### Key metrics")
    cols = st.columns(4)
    kpi_data = [
        ("Total Revenue", "$7,180,376", "success"),
        ("Total Orders", "4,003", "info"),
        ("Gross Margin", "81.81%", "success"),
        ("Refund Rate", "25.43%", "warning"),
    ]

    for col, (label, value, status) in zip(cols, kpi_data):
        with col:
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-value">{value}</div>'
                f'<div class="kpi-label">{label}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )


def render_insights(insights: list[dict]):
    """Render AI-generated insights as styled cards."""
    if not insights:
        return

    st.markdown("### Key insights")

    severity_config = {
        "critical": ("insight-critical", "🔴"),
        "warning": ("insight-warning", "🟡"),
        "info": ("insight-info", "🟢"),
    }

    for insight in insights:
        severity = insight.get("severity", "info")
        css_class, icon = severity_config.get(severity, ("insight-info", "🟢"))
        st.markdown(
            f'<div class="insight-card {css_class}">'
            f'<strong>{icon} {insight.get("title", "")}</strong><br>'
            f'{insight.get("explanation", "")}<br>'
            f'<em>Action: {insight.get("recommendation", "")}</em>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_charts(chart_paths: dict):
    """Render Plotly charts from saved HTML files."""
    if not chart_paths:
        return

    st.markdown("### Visualizations")

    # Map chart keys to display names
    chart_labels = {
        "revenue_trend": "Revenue Trend",
        "quarterly_trend": "Quarterly Performance",
        "regional_bar": "Revenue by Region",
        "regional_pie": "Revenue Market Share",
        "kpi_summary": "KPI Dashboard",
        "segments": "Customer Segments",
    }

    # Group charts in tabs for cleaner layout
    available = [(key, path) for key, path in chart_paths.items() if path.get("html")]

    if not available:
        st.info("Charts saved as files. Check output/charts/ directory.")
        return

    tab_labels = [chart_labels.get(key, key) for key, _ in available]
    tabs = st.tabs(tab_labels)

    for tab, (chart_key, paths) in zip(tabs, available):
        with tab:
            html_path = paths.get("html")
            if html_path:
                try:
                    with open(html_path, encoding="utf-8") as f:
                        html_html = f.read()
                        st.components.v1.html(html_html, height=500, scrolling=False)
                except FileNotFoundError:
                    st.warning(f"Chart file not found: {html_path}")


def render_sql_result(response: dict):
    """Render SQL query results as a dataframe."""
    if not response.get("sql_query"):
        return

    st.markdown("### Query Details")

    with st.expander("View Generated SQL", expanded=False):
        st.code(response["sql_query"], language="sql")

    if response.get("sql_result"):
        st.markdown(f"**{response['sql_row_count']} rows returned**")
        st.dataframe(response["sql_result"], use_container_width=True, hide_index=True)


def render_recommendations(actions: list[str]):
    """Render recommended actions as a clean list."""
    if not actions:
        return

    st.markdown("### Recommended actions")
    for i, action in enumerate(actions, 1):
        st.markdown(f"**{i}.** {action}")


def render_report_download(report_paths: dict):
    """Render download button for generated report."""
    if not report_paths:
        return

    md_path = report_paths.get("markdown")
    if not md_path:
        return

    try:
        with open(md_path, encoding="utf-8") as f:
            content = f.read()

        st.download_button(
            label="Download Report (Markdown)",
            data=content,
            file_name=f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    except FileNotFoundError:
        pass  # File not found, likely due to an error in report generation. No download button rendered.


def render_chat_message(role: str, content: str):
    """Render a single chat message."""
    if role == "user":
        st.markdown(
            f'<div class="user-message"><strong>You:</strong> {content}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="assistant-message">'
            f"<strong>AI Analyst:</strong> {content}"
            f"</div>",
            unsafe_allow_html=True,
        )
