"""
Seed script — generates realistic business sample data.
Run once to populate the database for development.

Usage:
    python scripts/seed_data.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.data.database import Base, engine, session_local
from app.data.models.business import Customer, Order, OrderItem, Product, SalesMetric

random.seed(42)  # for reproducibility

# Configuration for synthetic data generation
REGIONS = ["North", "South", "East", "West"]
SEGMENTS = ["enterprise", "smb", "consumer"]
CHANNELS = ["online", "in-store", "partner"]
STATUSES = [
    "completed",
    "completed",
    "completed",
    "refunded",
    "pending",
]  # more weight on completed orders for realism

PRODUCTS_DATA = [
    ("Analytics Pro", "Software", "BI Tools", 299.0, 45.0),
    ("Analytics Basic", "Software", "BI Tools", 99.0, 15.0),
    ("Data Pipeline Suite", "Software", "ETL", 499.0, 75.0),
    ("Cloud Storage 1TB", "Infrastructure", "Storage", 149.0, 30.0),
    ("Cloud Storage 5TB", "Infrastructure", "Storage", 599.0, 110.0),
    ("API Gateway", "Infrastructure", "Networking", 199.0, 40.0),
    ("ML Model Hosting", "AI Services", "Compute", 399.0, 80.0),
    ("AutoML Platform", "AI Services", "ML", 799.0, 150.0),
    ("Support Basic", "Services", "Support", 49.0, 5.0),
    ("Support Enterprise", "Services", "Support", 199.0, 20.0),
    ("Training Credits", "Services", "Education", 299.0, 25.0),
    ("Consulting Day", "Services", "Professional", 1200.0, 200.0),
]

CUSTOMER_NAMES = [
    "Acme Corp",
    "TechNova",
    "DataFlow Inc",
    "Bright Analytics",
    "Summit Systems",
    "Apex Digital",
    "CoreTech",
    "NexGen Solutions",
    "Vertex AI Labs",
    "Pinnacle Data",
    "Quantum Systems",
    "Horizon Tech",
    "Atlas Computing",
    "Meridian Software",
    "Zenith Analytics",
    "Catalyst Corp",
    "Momentum Tech",
    "Elevate Systems",
    "Fusion Data",
    "Clarity Analytics",
    "Synergy Corp",
    "Pioneer Tech",
    "Vanguard AI",
    "Eclipse Systems",
    "Nova Analytics",
    "Stellar Data",
    "Orbit Tech",
    "Cosmo Computing",
    "Nebula Systems",
    "Pulsar Analytics",
]


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully.")


def seed_products(db: Session) -> list[Product]:
    products = []
    for name, category, subcategory, price, cost in PRODUCTS_DATA:
        product = Product(
            name=name,
            category=category,
            subcategory=subcategory,
            unit_price=price,
            cost_price=cost,
        )
        db.add(product)
        products.append(product)
    db.commit()
    print(f"✓ Seeded {len(products)} products.")
    return products


def seed_customers(db: Session) -> list[Customer]:
    customers = []
    base_date = datetime(2025, 1, 1)
    for i, name in enumerate(CUSTOMER_NAMES * 5):  # 150 customers
        signup_offset = random.randint(0, 500)  # customers signed up over ~1.5 years
        customer = Customer(
            name=f"{name} {i+1}",
            email=f"contact{i+1}@{name.lower().replace(' ', '')}.com",
            region=random.choice(REGIONS),
            segment=random.choice(SEGMENTS),
            signup_date=base_date + timedelta(days=signup_offset),
            is_active=random.random() > 0.15,  # 85% active
        )
        db.add(customer)
        customers.append(customer)

    db.commit()
    print(f"✓ Seeded {len(customers)} customers.")
    return customers


def seed_orders(
    db: Session, customers: list[Customer], products: list[Product]
) -> None:
    """
    Generate 18 months of order history with realistic patterns:
    - Q4 seasonal spikes
    - Q2 dip (realistic business cycle)
    - Regional variation
    - Weekend drop-off
    """
    base_date = datetime(2025, 1, 1)
    orders_created = 0
    items_created = 0

    for day_offset in range(0, 540):  # 18 months
        current_date = base_date + timedelta(days=day_offset)

        # fewer orders on weekends
        if current_date.weekday() >= 5:
            daily_orders = random.randint(2, 6)
        else:
            daily_orders = random.randint(8, 20)

        # seasonal spike in Q4
        if current_date.month in [10, 11, 12]:
            daily_orders = int(daily_orders * random.uniform(1.5, 2.5))

        # Q2 dip
        if current_date.month in [4, 5, 6]:
            daily_orders = int(daily_orders * random.uniform(0.7, 0.9))

        for _ in range(daily_orders):
            customer = random.choice(customers)
            num_items = random.randint(1, 4)
            selected_products = random.sample(products, min(num_items, len(products)))
            total_amount = 0.0
            discount_amount = round(random.uniform(0, 50), 2)  # up to $50 discount
            order_items_data = []

            for product in selected_products:
                qty = random.randint(1, 3)
                discount_pct = random.choice(
                    [0, 0.05, 0.1, 0.15]
                )  # 0%, 5%, 10%, 15% discount
                line_total = round(product.unit_price * qty * (1 - discount_pct), 2)
                total_amount += line_total
                order_items_data.append((product, qty, discount_pct, line_total))

            order = Order(
                customer_id=customer.id,
                order_date=current_date,
                status=random.choice(STATUSES),
                region=customer.region,
                sales_channel=random.choice(CHANNELS),
                total_amount=round(total_amount - discount_amount, 2),
                discount_amount=discount_amount,
            )
            db.add(order)
            db.flush()  # get order.id for items

            for product, qty, discount_pct, line_total in order_items_data:
                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=product.unit_price,
                    discount_pct=discount_pct,
                    line_total=line_total,
                )
                db.add(item)
                items_created += 1

            orders_created += 1

        if day_offset % 90 == 0:  # commit every 90 days to avoid long transactions
            db.commit()
            print(f" -> {orders_created} orders created so far...")

    db.commit()
    print(f"✓ Seeded {orders_created} orders with {items_created} items.")


def seed_sales_metrics(db: Session) -> None:
    """
    Pre-aggregate daily sales metrics for faster dashboard queries.
    """
    # This is a simplified example. In a real scenario, you might want to calculate more complex metrics.
    from sqlalchemy import text

    db.execute(text("""DELETE FROM sales_metrics"""))  # clear existing metrics

    result = db.execute(
        text("""
        SELECT
            DATE(o.order_date)  AS date,
            o.region            AS region,
            p.category          AS category,
            SUM(oi.line_total)  AS total_revenue,
            COUNT(DISTINCT o.id) AS total_orders,
            COUNT(DISTINCT o.customer_id) AS total_customers,
            AVG(o.total_amount) AS avg_order_value,
            SUM(p.cost_price * oi.quantity) AS total_cost
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE o.status = 'completed'
        GROUP BY DATE(o.order_date), o.region, p.category
    """)
    )  # select completed orders and aggregate by day, region, category

    rows = result.fetchall()
    for row in rows:
        metric = SalesMetric(
            date=datetime.strptime(str(row[0]), "%Y-%m-%d"),
            region=row[1],
            category=row[2],
            total_revenue=round(row[3], 2),
            total_orders=row[4],
            total_customers=row[5],
            avg_order_value=round(row[6], 2),
            total_cost=round(row[7], 2),
            gross_profit=round(row[3] - row[7], 2),
        )
        db.add(metric)

    db.commit()
    print(f"✓ Seeded {len(rows)} aggregated daily metric rows")


def main():
    print("Starting data seeding...")
    create_tables()

    db: Session = session_local()
    try:
        seed_products(db)
        customers = seed_customers(db)
        products = db.query(Product).all()  # re-query to get IDs
        seed_orders(db, customers, products)
        seed_sales_metrics(db)
        print("\n ✅ Database seeded successfully.")
        print(
            "  Run the app and start quering your data analyst with natural language questions! 🚀"
        )
    except Exception as e:
        print(f"\n ❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
