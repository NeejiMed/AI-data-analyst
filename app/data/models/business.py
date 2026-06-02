from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.data.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    region = Column(String(50), nullable=False)
    segment = Column(String(50), nullable=False)  # enterprise, SMB, consumer
    signup_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    orders = relationship("Order", back_populates="customer")

    __table_args__ = (
        Index("ix_customers_region", "region"),
        Index("ix_customers_segment", "segment"),
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    unit_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    order_items = relationship("OrderItem", back_populates="product")

    __table_args__ = (Index("ix_products_category", "category"),)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)  # completed, refunded, pending
    region = Column(String(50), nullable=False)
    sales_channel = Column(String(50), nullable=False)  # online, in-store, partner
    total_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

    __table_args__ = (
        Index("ix_orders_customer_id", "customer_id"),
        Index("ix_orders_order_date", "order_date"),
        Index("ix_orders_region", "region"),
        Index("ix_orders_status", "status"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_pct = Column(Float, default=0.0)  # percentage discount on this item
    line_total = Column(
        Float, nullable=False
    )  # calculated as quantity * unit_price * (1 - discount_pct/100)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    __table_args__ = (
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_product_id", "product_id"),
    )


class SalesMetric(Base):
    """
    Pre-aggregated sales metrics for faster querying. This table can be populated by a scheduled job that runs daily/weekly.
    Used for fast dashboard queries without scanning all orders.
    """

    __tablename__ = "sales_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    region = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)
    total_revenue = Column(Float, nullable=False)
    total_orders = Column(Integer, nullable=False)
    total_customers = Column(Integer, nullable=False)
    avg_order_value = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    gross_profit = Column(Float, nullable=False)

    __table_args__ = (
        Index("ix_sales_metrics_date", "date"),
        Index("ix_sales_metrics_region", "region"),
    )
