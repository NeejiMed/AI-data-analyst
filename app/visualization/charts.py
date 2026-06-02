"""
Chart generation using plotly.
Each function takes structured data and returns a Plotly figure.
Figures can be saved as static PNG or interactive HTML files.
Design principles:
- each chart function is pure (same input -> same output) which makes them easy to test and reuse.
- no side effects ( saving is handled by the engine, not the chart functions).
- Consistent styling across charts (colors, fonts, layout) for a cohesive report appearance.
"""

import plotly.graph_objects as go
import structlog
from plotly.subplots import make_subplots

logger = structlog.get_logger()

# -- Design system --
COLORS = {
    "primary": "#2C3E50",
    "secondary": "#3498DB",
    "success": "#27AE60",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "regions": ["#3498DB", "#27AE60", "#F39C12", "#E74C3C"],
    "segments": ["#2ECC71", "#3498DB", "#F39C12", "#E67E22", "#E74C3C"],
}

LAYOUT_DEFAULTS = {
    "font_family": "Inter, Arial, sans-serif",
    "font_size": 12,
    "plot_bgcolor": "white",
    "paper_bgcolor": "white",
    "margin": {"t": 60, "b": 60, "l": 60, "r": 40},
    "hoverlabel": {"bgcolor": "white", "font_size": 12},
}


def revenue_trend_chart(
    monthly_trends: list, title: str = "Monthly Revenue Trends"
) -> go.Figure:
    """
    Line chart of monthly revenue with anomaly markers highlighted.
    anomalous months are marked with distinct colors and larger markers.
    """
    labels = [m.month_label for m in monthly_trends]
    revenues = [m.total_revenue for m in monthly_trends]
    is_anomaly = [m.is_anomaly for m in monthly_trends]

    # Split into normal and anomaly points for separate traces
    normal_x = [lbl for lbl, a in zip(labels, is_anomaly) if not a]
    normal_y = [r for r, a in zip(revenues, is_anomaly) if not a]
    anomaly_x = [lbl for lbl, a in zip(labels, is_anomaly) if a]
    anomaly_y = [r for r, a in zip(revenues, is_anomaly) if a]

    fig = go.Figure()

    # Main revenue line
    fig.add_trace(
        go.Scatter(
            x=labels,
            y=revenues,
            mode="lines",
            name="Revenue",
            line={"color": COLORS["secondary"], "width": 2},
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>",
        )
    )

    # Normal data points
    fig.add_trace(
        go.Scatter(
            x=normal_x,
            y=normal_y,
            mode="markers",
            name="Normal",
            marker={"color": COLORS["secondary"], "size": 6},
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>",
        )
    )

    # Anomaly data - highlighted in red
    if anomaly_x:
        fig.add_trace(
            go.Scatter(
                x=anomaly_x,
                y=anomaly_y,
                mode="markers",
                name="Anomaly",
                marker={
                    "color": COLORS["danger"],
                    "size": 12,
                    "symbol": "diamond",
                    "line": {"color": "white", "width": 2},
                },
                hovertemplate=(
                    "<b>%{x}</b><br>Revenue: $%{y:,.2f}"
                    "<br><b>ANOMALY DETECTED</b><extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title={"text": title, "font": {"size": 16}},
        xaxis_title="Month",
        yaxis_title="Revenue ($)",
        yaxis_tickformat="$,.0f",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        **LAYOUT_DEFAULTS,
    )

    logger.info("Revenue_trend_chart_generated", type="revenue_trend")
    return fig


def regional_revenue_chart(regional_kpis: list, chart_type: str = "bar") -> go.Figure:
    """
    Bar or pie chart showing revenue by region.
    Bar shows absolute values, pie shows market share.
    """
    regions = [k.region for k in regional_kpis]
    revenues = [k.total_revenue for k in regional_kpis]

    if chart_type == "pie":
        fig = go.Figure(
            go.Pie(
                labels=regions,
                values=revenues,
                marker_colors=COLORS["regions"],
                textinfo="label+percent",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Revenue: $%{value:,.2f}<br>"
                    "Share: %{percent}<extra></extra>"
                ),
            )
        )
        fig.update_layout(
            title={"text": "Revenue by Region", "font": {"size": 16}}, **LAYOUT_DEFAULTS
        )
    else:  # default to bar
        fig = go.Figure(
            go.Bar(
                x=regions,
                y=revenues,
                marker_color=COLORS["regions"],
                text=[f"${r:,.0f}" for r in revenues],
                textposition="outside",
                hovertemplate=("<b>%{x}</b><br>" "Revenue: $%{y:,.2f}<extra></extra>"),
            )
        )
        fig.update_layout(
            title={"text": "Revenue by Region", "font": {"size": 16}},
            xaxis_title="Region",
            yaxis_title="Revenue ($)",
            yaxis_tickformat="$,.0f",
            **LAYOUT_DEFAULTS,
        )

    logger.info("chart_created", type=f"regional_{chart_type}")
    return fig


def quarterly_trend_chart(quarterly_trends: list) -> go.Figure:
    """
    Combined bar & line chart showing quarterly revenue and growth rate.
    uses dual y-axes: revenue on left, growth rate on right.
    """
    quarters = [q.quarter_label for q in quarterly_trends]
    revenues = [q.total_revenue for q in quarterly_trends]
    growth = [
        q.revenue_growth_pct if q.revenue_growth_pct is not None else 0
        for q in quarterly_trends
    ]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Revenue bars
    fig.add_trace(
        go.Bar(
            x=quarters,
            y=revenues,
            name="Revenue",
            marker_color=COLORS["secondary"],
            opacity=0.8,
            hovertemplate=("<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>"),
        ),
        secondary_y=False,
    )

    # Growth line
    fig.add_trace(
        go.Scatter(
            x=quarters,
            y=growth,
            name="Growth Rate",
            mode="lines+markers",
            line={"color": COLORS["warning"], "width": 2},
            marker={"size": 8},
            hovertemplate=("<b>%{x}</b><br>Growth Rate: %{y:.1f}%<extra></extra>"),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title={"text": "Quarterly Revenue & Growth", "font": {"size": 16}},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        **LAYOUT_DEFAULTS,
    )
    fig.update_yaxes(
        title_text="Revenue ($)",
        tickformat="$,.0f",
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Growth Rate (%)",
        ticksuffix="%",
        secondary_y=True,
    )

    logger.info("Quarterly_trend_chart_generated", type="quarterly_trend")
    return fig


def customer_segment_chart(segments: list) -> go.Figure:
    """
    Horizontal bar chart showing revenue of customer segments by count and revenue.
    shows both volum and value side by side.
    """
    if not segments:
        fig = go.Figure()
        fig.update_layout(title="No segment data available")
        return fig

    segment_names = [s.segment_name for s in segments]
    counts = [s.customer_count for s in segments]
    revenues = [s.avg_revenue for s in segments]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Customers by Segment", "Avg Revenue by Segment"),
    )

    fig.add_trace(
        go.Bar(
            y=segment_names,
            x=counts,
            orientation="h",
            marker_color=COLORS["segments"],
            text=counts,
            textposition="outside",
            hovertemplate=("<b>%{y}</b><br>Customers: %{x}<extra></extra>"),
            name="Count",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            y=segment_names,
            x=revenues,
            orientation="h",
            marker_color=COLORS["segments"],
            text=[f"${r:,.0f}" for r in revenues],
            textposition="outside",
            hovertemplate=("<b>%{y}</b><br>Avg Revenue: $%{x:,.2f}<extra></extra>"),
            name="Avg Revenue",
        ),
        row=1,
        col=2,
    )

    fig.update_layout(
        title={"text": "Customer Segmentation Analysis", "font": {"size": 16}},
        showlegend=False,
        **LAYOUT_DEFAULTS,
    )

    logger.info("chart_created", type="customer_segments")
    return fig


def kpi_summary_chart(revenue_kpis) -> go.Figure:
    """
    KPI gauge/indicator summary chart.
    Shows key metrics as visual indicators with target comparisons.
    """
    fig = make_subplots(
        rows=1,
        cols=3,
        specs=[
            [
                {"type": "indicator"},
                {"type": "indicator"},
                {"type": "indicator"},
            ]
        ],
    )

    # Gross margin gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=revenue_kpis.gross_margin_pct,
            title={"text": "Gross Margin"},
            number={"suffix": "%"},
            delta={"reference": 75, "valueformat": ".1f"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": COLORS["success"]},
                "steps": [
                    {"range": [0, 60], "color": "#FADBD8"},
                    {"range": [60, 75], "color": "#FDEBD0"},
                    {"range": [75, 100], "color": "#D5F5E3"},
                ],
                "threshold": {
                    "line": {"color": COLORS["primary"], "width": 3},
                    "thickness": 0.75,
                    "value": 75,
                },
            },
        ),
        row=1,
        col=1,
    )

    # Refund rate gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=revenue_kpis.refund_rate_pct,
            title={"text": "Refund Rate"},
            number={"suffix": "%"},
            delta={
                "reference": 15,
                "valueformat": ".1f",
                "increasing": {"color": COLORS["danger"]},
            },
            gauge={
                "axis": {"range": [0, 50]},
                "bar": {"color": COLORS["danger"]},
                "steps": [
                    {"range": [0, 15], "color": "#D5F5E3"},
                    {"range": [15, 25], "color": "#FDEBD0"},
                    {"range": [25, 50], "color": "#FADBD8"},
                ],
                "threshold": {
                    "line": {"color": COLORS["primary"], "width": 3},
                    "thickness": 0.75,
                    "value": 15,
                },
            },
        ),
        row=1,
        col=2,
    )

    # AOV indicator
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=revenue_kpis.avg_order_value,
            title={"text": "Avg Order Value"},
            number={"prefix": "$", "valueformat": ",.2f"},
            delta={"reference": 1500, "valueformat": ".0f"},
        ),
        row=1,
        col=3,
    )

    fig.update_layout(
        title={"text": "KPI Dashboard", "font": {"size": 16}},
        height=300,
        **LAYOUT_DEFAULTS,
    )

    logger.info("chart_created", type="kpi_summary")
    return fig
