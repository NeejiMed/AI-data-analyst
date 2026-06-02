"""Quick sanity check on seeded data."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func

from app.data.database import SessionLocal
from app.data.models.business import Customer, Order, OrderItem, Product, SalesMetric

db = SessionLocal()

print("=== Database Verification ===")
print(f"Customers:    {db.query(func.count(Customer.id)).scalar()}")
print(f"Products:     {db.query(func.count(Product.id)).scalar()}")
print(f"Orders:       {db.query(func.count(Order.id)).scalar()}")
print(f"Order items:  {db.query(func.count(OrderItem.id)).scalar()}")
print(f"Daily metrics:{db.query(func.count(SalesMetric.id)).scalar()}")

total_revenue = (
    db.query(func.sum(Order.total_amount)).filter(Order.status == "completed").scalar()
)
print(f"\nTotal revenue (completed): ${total_revenue:,.2f}")

print("\nRevenue by region:")
results = (
    db.query(Order.region, func.sum(Order.total_amount).label("revenue"))
    .filter(Order.status == "completed")
    .group_by(Order.region)
    .order_by(func.sum(Order.total_amount).desc())
    .all()
)

for region, revenue in results:
    print(f"  {region}: ${revenue:,.2f}")

db.close()
