-- fact_customer_services: service bridge — one row per (customer, service).
--
-- "Rows, not columns": each customer's subscribed services unpack into rows
-- joined to dim_service by service_name. Grain: (customer_id, service_key).
with base as (
    select * from {{ ref('stg_telco_churn') }}
),

customer_services as (
    select customer_id, 'phone_service' as service_name,
           phone_service = 'yes' as subscribed
    from base
    union all
    select customer_id, 'multiple_lines', multiple_lines = 'yes'
    from base
    union all
    select customer_id, 'internet_dsl', internet_service = 'dsl'
    from base
    union all
    select customer_id, 'internet_fiber', internet_service = 'fiber optic'
    from base
    union all
    select customer_id, 'online_security', online_security = 'yes'
    from base
    union all
    select customer_id, 'online_backup', online_backup = 'yes'
    from base
    union all
    select customer_id, 'device_protection', device_protection = 'yes'
    from base
    union all
    select customer_id, 'tech_support', tech_support = 'yes'
    from base
    union all
    select customer_id, 'streaming_tv', streaming_tv = 'yes'
    from base
    union all
    select customer_id, 'streaming_movies', streaming_movies = 'yes'
    from base
)

select
    cs.customer_id,
    ds.service_key,
    cs.subscribed
from customer_services cs
join {{ ref('dim_service') }} ds using (service_name)
