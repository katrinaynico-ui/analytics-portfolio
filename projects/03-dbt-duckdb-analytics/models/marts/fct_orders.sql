-- Fact: orders (invoice grain) for revenue analytics.
select
    invoice_id as order_id,
    customer_id,
    order_ts,
    order_date,
    country,
    n_lines,
    n_items,
    n_products,
    order_revenue
from {{ ref('int_orders') }}
