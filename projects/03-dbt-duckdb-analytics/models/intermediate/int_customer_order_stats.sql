-- Per-customer order aggregates used by dim_customers / RFM.
with orders as (
    select * from {{ ref('int_orders') }}
),

stats as (
    select
        customer_id,
        min(order_date) as first_order_date,
        max(order_date) as last_order_date,
        count(*) as frequency,
        round(sum(order_revenue), 2) as monetary,
        round(avg(order_revenue), 2) as avg_order_value,
        sum(n_items) as n_items,
        sum(n_products) as n_product_lines
    from orders
    group by 1
)

select * from stats
