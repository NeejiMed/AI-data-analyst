"""
Visualization engine for generating and saving chart sets from analytics results.
"""

from pathlib import Path

import structlog

from app.analytics.engine import AnalyticsResult
from app.visualization.charts import (
    customer_segment_chart,
    kpi_summary_chart,
    quarterly_trend_chart,
    regional_revenue_chart,
    revenue_trend_chart,
)

logger = structlog.get_logger()

OUTPUT_DIR = Path("outputs/charts")


class VisualizationEngine:
    """
    Generates complete chart sets from AnalyticsResult objects.
    Returns both file paths (for reports) and plotly Figure objects (for interactive use).
    """

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save_chart(
        self, fig, filename: str, save_html: bool = True, save_png: bool = False
    ) -> dict[str, str]:
        """
        Save a Plotly figure as HTML and/or PNG, returning the file paths.
        """
        paths = {}
        if save_html:
            html_path = f"{self.output_dir}/{filename}.html"
            fig.write_html(html_path, include_plotlyjs="cdn", full_html=False)
            paths["html"] = html_path

        if save_png:
            png_path = f"{self.output_dir}/{filename}.png"
            try:
                fig.write_image(png_path, width=1000, height=500, scale=2)
                paths["png"] = png_path
            except Exception as e:
                logger.warning(
                    "png_export_skipped",
                    filename=filename,
                    error=str(e),
                )

        return paths

    def generate_sales_charts(self, result: AnalyticsResult, save: bool = True) -> dict:
        """
        Generate full chart set for a sales trend analysis result.

        Returns:
            Dict with chart names as keys, each containing
            'figure' (Plotly fig) and 'paths' (saved file paths)
        """
        logger.info("generating_sales_charts")
        charts = {}

        # 1. Revenue Trend with anomaly markers
        if result.monthly_trends:
            fig = revenue_trend_chart(result.monthly_trends)
            paths = self._save_chart(fig, "revenue_trend") if save else {}
            charts["revenue_trend"] = {"figure": fig, "paths": paths}

        # 2. Regional Revenue bar chart
        if result.regional_kpis:
            fig = regional_revenue_chart(result.regional_kpis, "bar")
            paths = self._save_chart(fig, "regional_revenue_bar") if save else {}
            charts["regional_bar"] = {"figure": fig, "paths": paths}

            fig_pie = regional_revenue_chart(result.regional_kpis, "pie")
            paths_pie = (
                self._save_chart(fig_pie, "regional_revenue_pie") if save else {}
            )
            charts["regional_pie"] = {"figure": fig_pie, "paths": paths_pie}

        # 3. Quarterly trend with growth rate
        if result.quarterly_trends:
            fig = quarterly_trend_chart(result.quarterly_trends)
            paths = self._save_chart(fig, "quarterly_trend") if save else {}
            charts["quarterly_trend"] = {"figure": fig, "paths": paths}

        # 4. KPI gauges chart
        if result.revenue_kpis:
            fig = kpi_summary_chart(result.revenue_kpis)
            paths = self._save_chart(fig, "kpi_summary", save_png=False) if save else {}
            charts["kpi_summary"] = {"figure": fig, "paths": paths}

        logger.info("sales_charts_generated", count=len(charts))
        return charts

    def generate_segmentation_charts(
        self, result: AnalyticsResult, save: bool = True
    ) -> dict:
        """
        Generate customer segmentation charts from an AnalyticsResult.

        Returns:
            Dict with chart names as keys, each containing
            'figure' (Plotly fig) and 'paths' (saved file paths)
        """
        charts = {}

        if result.segments:
            fig = customer_segment_chart(result.segments)
            paths = self._save_chart(fig, "customer_segments") if save else {}
            charts["customer_segments"] = {"figure": fig, "paths": paths}

        return charts
