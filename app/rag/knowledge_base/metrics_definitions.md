# Metrics Definitions & Calculation Methods

## Revenue Metrics

### Gross Revenue
Sum of total_amount for all completed orders in the period.
Formula: SUM(orders.total_amount) WHERE status = 'completed'

### Net Revenue
Gross revenue minus refunds.
Formula: Gross Revenue - SUM(refunded order amounts)

### Gross Profit
Revenue minus cost of goods sold.
Formula: total_revenue - SUM(products.cost_price * order_items.quantity)

### Gross Margin
Gross profit as a percentage of revenue.
Formula: (gross_profit / total_revenue) * 100

## Customer Metrics

### Average Order Value (AOV)
Mean transaction value for completed orders.
Formula: total_revenue / total_orders

### Customer Lifetime Value (CLV)
Estimated total revenue from a customer over their relationship.
Approximation: avg_order_value * avg_order_frequency * avg_customer_lifespan_years

### RFM Scoring
- Recency (R): Days since last purchase — lower is better
- Frequency (F): Number of completed orders — higher is better
- Monetary (M): Total spend — higher is better
- Combined score 1–12: Champions (10–12), Loyal (8–9),
  Promising (6–7), At Risk (4–5), Lost (1–3)

## Anomaly Detection

### Z-Score Method
Used for monthly revenue anomaly detection.
z = (value - mean) / std_deviation
Threshold: |z| > 1.5 flagged as anomaly
Severity: |z| > 2.5 = high, |z| > 2.0 = medium, else low

### Expected Seasonal Adjustment
When interpreting Q4 spikes, note that increases up to 60% above
quarterly average are within normal seasonal range and should not
be treated as anomalies requiring investigation.
