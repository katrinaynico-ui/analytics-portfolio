-- Dimension: one row per customer with order lifetime stats.
with stats as (
    select * from {{ ref('int_customer_order_stats') }}
),

countries as (
    select
        customer_id,
        mode(country) as primary_country
    from {{ ref('int_orders') }}
    group by 1
)

select
    s.customer_id,
    c.primary_country as country,
    s.first_order_date,
    s.last_order_date,
    s.frequency,
    s.monetary,
    s.avg_order_value,
    s.n_items,
    date_diff('day', s.first_order_date, s.last_order_date) as tenure_days
from stats s
left join countries c using (customer_id)
