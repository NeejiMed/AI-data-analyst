"""
Custom CSS for the Streamlit frontend.
Keeps styling separate from logic.
"""

CUSTOM_CSS = """
<style>
    /* Main layout */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Chat message styling */
    .user-message {
        background: #EBF5FB;
        border-left: 4px solid #3498DB;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        color: #000000 !important;
    }

    .user-message * {
        color: #000000 !important;
    }

    .assistant-message {
        background: #F8F9FA;
        border-left: 4px solid #27AE60;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        color: #000000 !important;
    }

    .assistant-message * {
        color: #000000 !important;
    }

    /* KPI cards */
    .kpi-card {
        background: white;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2C3E50;
    }

    .kpi-label {
        font-size: 0.85rem;
        color: #7F8C8D;
        margin-top: 4px;
    }

    /* Insight cards */
    .insight-card {
        border-radius: 8px;
        padding: 14px 16px;
        margin: 8px 0;
        border-left: 4px solid;
    }

    .insight-critical {
        background: #FDEDEC;
        border-color: #E74C3C;
    }

    .insight-warning {
        background: #FEF9E7;
        border-color: #F39C12;
    }

    .insight-info {
        background: #EBF5FB;
        border-color: #3498DB;
    }

    /* Sidebar */
    .sidebar-header {
        font-size: 0.75rem;
        font-weight: 600;
        color: #7F8C8D;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }

    /* Status badges */
    .badge-success {
        background: #D5F5E3;
        color: #1E8449;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .badge-warning {
        background: #FEF9E7;
        color: #B7770D;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .badge-danger {
        background: #FDEDEC;
        color: #922B21;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
