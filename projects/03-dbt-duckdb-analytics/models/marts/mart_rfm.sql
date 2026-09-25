-- Mart: RFM scores + transparent rule-based segments (recomputed in dbt SQL).
-- Recency = days between last order and var rfm_as_of_date.
{% set as_of = var('rfm_as_of_date') %}

with base as (
    select
        customer_id,
        frequency,
        monetary,
        last_order_date,
        date_diff('day', last_order_date, date '{{ as_of }}') as recency
    from {{ ref('dim_customers') }}
),

scored as (
    select
        *,
        ntile(5) over (order by recency asc) as r_score,   -- lower recency → higher score via reverse below
        ntile(5) over (order by frequency asc) as f_score,
        ntile(5) over (order by monetary asc) as m_score
    from base
),

-- Invert R so 5 = most recent (smallest recency)
rfm as (
    select
        customer_id,
        recency,
        frequency,
        monetary,
        last_order_date,
        (6 - r_score) as r_score,
        f_score,
        m_score,
        (6 - r_score) + f_score + m_score as rfm_score
    from scored
),

segmented as (
    select
        *,
        case
            when r_score >= 4 and f_score >= 4 and m_score >= 4 then 'Champions'
            when r_score >= 3 and f_score >= 3 and m_score >= 4 then 'Loyal'
            when r_score >= 4 and f_score <= 2 then 'New / Promising'
            when r_score <= 2 and f_score >= 3 and m_score >= 3 then 'At Risk'
            when r_score <= 2 and f_score <= 2 then 'Hibernating'
            when m_score = 5 and f_score <= 2 then 'Big Spenders'
            else 'Need Attention'
        end as segment
    from rfm
)

select * from segmented
