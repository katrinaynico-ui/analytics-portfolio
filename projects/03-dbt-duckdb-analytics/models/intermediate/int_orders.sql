-- Order grain: one row per invoice (order).
with lines as (
    select * from {{ ref('stg_transactions') }}
),

orders as (
    select
        invoice_id,
        customer_id,
        min(invoice_ts) as order_ts,
        min(invoice_date) as order_date,
        max(country) as country,
        count(*) as n_lines,
        sum(quantity) as n_items,
        count(distinct stock_code) as n_products,
        round(sum(line_revenue), 2) as order_revenue
    from lines
    group by 1, 2
)

select * from orders
