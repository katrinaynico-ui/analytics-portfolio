-- Staging: normalize column names + types from the warehouse seed.
with source as (
    select * from {{ source('retail_raw', 'transactions_clean') }}
),

renamed as (
    select
        cast(InvoiceNo as varchar) as invoice_id,
        cast(StockCode as varchar) as stock_code,
        cast(Description as varchar) as description,
        cast(Quantity as integer) as quantity,
        cast(InvoiceDate as timestamp) as invoice_ts,
        cast(InvoiceDate as date) as invoice_date,
        cast(UnitPrice as double) as unit_price,
        cast(CustomerID as integer) as customer_id,
        cast(Country as varchar) as country,
        cast(line_revenue as double) as line_revenue
    from source
)

select * from renamed
