-- Custom singular test: no NULL total_charges after the business rule.
-- (The source has 11 blank TotalCharges rows — tenure-0 customers. Staging
-- must apply total_charges = 0 for tenure 0; this test fails loudly if it
-- doesn't.)
select *
from {{ ref('stg_telco_churn') }}
where total_charges is null
