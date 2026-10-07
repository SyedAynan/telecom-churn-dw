-- mart_customer_360: analytics-ready flat table, one row per customer.
-- Grain: customer_id. Joins fact_customer to dims + pivots the service
-- bridge back into flags (for the ML model and dashboard convenience).
with services as (
    select
        customer_id,
        sum(case when service_key = 1 then 1 else 0 end)  as n_phone_services,
        count(*) filter (where category = 'internet' and subscribed) as n_internet,
        count(*) filter (where category = 'addon' and subscribed)   as n_addons
    from {{ ref('fact_customer_services') }} fcs
    join {{ ref('dim_service') }} ds using (service_key)
    group by customer_id
)

select
    fc.customer_id,
    fc.tenure_months,
    fc.monthly_charges,
    fc.total_charges,
    fc.churned,
    fc.is_female,
    fc.is_senior,
    fc.has_partner,
    fc.has_dependents,
    fc.paperless_billing,
    dc.contract_label,
    dc.contract_months,
    dpm.payment_method_label,
    dpm.payment_automation,
    s.n_phone_services,
    s.n_internet,
    s.n_addons,
    case
        when fc.tenure_months <= 12 then '0-12'
        when fc.tenure_months <= 24 then '13-24'
        when fc.tenure_months <= 48 then '25-48'
        else '49-72'
    end as tenure_bucket,
    case
        when fc.monthly_charges < 35 then 'a. < 35'
        when fc.monthly_charges < 60 then 'b. 35-59.99'
        when fc.monthly_charges < 85 then 'c. 60-84.99'
        else 'd. >= 85'
    end as monthly_charge_band
from {{ ref('fact_customer') }} fc
join {{ ref('dim_contract') }} dc on fc.contract_key = dc.contract_key
join {{ ref('dim_payment_method') }} dpm on fc.payment_method_key = dpm.payment_method_key
join services s on fc.customer_id = s.customer_id
