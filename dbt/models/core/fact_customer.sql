-- fact_customer: one row per customer.
-- Grain: customer_id. Measures: tenure, charges. Degenerate dimensions:
-- churn flag, demographic flags. FKs to dim_contract, dim_payment_method,
-- dim_date (customer start month derived from tenure).
with base as (
    select * from {{ ref('stg_telco_churn') }}
)

select
    customer_id,
    -- as-of date 2020-02-01 minus tenure; rounded to month start
    date_trunc(
        'month',
        date '2020-02-01' - (tenure_months || ' months')::interval
    )::date                                        as start_month_key,
    contract_type                                  as contract_key,
    payment_method                                 as payment_method_key,
    tenure_months,
    monthly_charges,
    total_charges,
    case churned when 'yes' then true else false end as churned,
    case gender when 'female' then true else false end as is_female,
    senior_citizen = 1                              as is_senior,
    has_partner = 'yes'                             as has_partner,
    has_dependents = 'yes'                          as has_dependents,
    paperless_billing = 'yes'                       as paperless_billing
from base
