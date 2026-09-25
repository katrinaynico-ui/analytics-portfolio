-- Mart: daily revenue KPIs (warehouse-style reporting table).
select
    order_date as revenue_date,
    count(*) as n_orders,
    count(distinct customer_id) as n_customers,
    sum(n_items) as n_items,
    round(sum(order_revenue), 2) as daily_revenue,
    round(avg(order_revenue), 2) as avg_order_value
from {{ ref('fct_orders') }}
group by 1
order by 1
