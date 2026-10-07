-- mart_churn_summary: churn rate by segment — one row per
-- (segment_type, segment_label) across four dimensions.
-- Grain: segment. This is the "at a glance" mart for the Overview page.
with base as (
    select * from {{ ref('mart_customer_360') }}
),

by_contract as (
    select 'contract' as segment_type, contract_label as segment_label,
           contract_label as sort_key
    from base group by 1, 2
),

by_payment as (
    select 'payment_method' as segment_type, payment_method_label as segment_label,
           payment_method_label as sort_key
    from base group by 1, 2
),

by_tenure as (
    select 'tenure_bucket' as segment_type, tenure_bucket as segment_label,
           tenure_bucket as sort_key
    from base group by 1, 2
),

by_charge as (
    select 'monthly_charge_band' as segment_type, monthly_charge_band as segment_label,
           monthly_charge_band as sort_key
    from base group by 1, 2
),

segments as (
    select * from by_contract
    union all select * from by_payment
    union all select * from by_tenure
    union all select * from by_charge
)

select
    seg.segment_type,
    seg.segment_label,
    count(b.customer_id)                                    as n_customers,
    count(b.customer_id) filter (where b.churned)          as n_churned,
    round(avg(b.churned::int), 4)                          as churn_rate
from segments seg
left join base b
    on (seg.segment_type = 'contract'          and b.contract_label = seg.segment_label)
    or (seg.segment_type = 'payment_method'    and b.payment_method_label = seg.segment_label)
    or (seg.segment_type = 'tenure_bucket'     and b.tenure_bucket = seg.segment_label)
    or (seg.segment_type = 'monthly_charge_band' and b.monthly_charge_band = seg.segment_label)
group by seg.segment_type, seg.segment_label
