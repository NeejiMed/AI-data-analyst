import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime  # noqa: E402

from app.analytics.engine import AnalyticsEngine  # noqa: E402
from app.data.database import SessionLocal  # noqa: E402
from app.visualization.engine import VisualizationEngine  # noqa: E402

print("=" * 60)
print("VISUALIZATION ENGINE TEST")
print("=" * 60)

db = SessionLocal()
analytics = AnalyticsEngine(db)
viz = VisualizationEngine()

# Sales trend charts
print("\n1. Generating sales trend charts...")
result = analytics.analyze_sales_trends(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2026, 6, 30),
)
charts = viz.generate_sales_charts(result)

for name, data in charts.items():
    paths = data["paths"]
    print(f"   {name}:")
    for fmt, path in paths.items():
        print(f"     {fmt}: {path}")

# Segmentation charts
print("\n2. Generating segmentation charts...")
seg_result = analytics.analyze_customer_segments(reference_date=datetime(2026, 6, 30))
seg_charts = viz.generate_segmentation_charts(seg_result)

for name, data in seg_charts.items():
    paths = data["paths"]
    print(f"   {name}:")
    for fmt, path in paths.items():
        print(f"     {fmt}: {path}")

print("\n3. Verifying output files...")
import os  # noqa: E402, F811

for fname in os.listdir("outputs/charts"):
    if fname != ".gitkeep":
        size = os.path.getsize(f"outputs/charts/{fname}")
        print(f"   {fname} ({size:,} bytes)")

db.close()
print("\nVisualization engine test complete.")
