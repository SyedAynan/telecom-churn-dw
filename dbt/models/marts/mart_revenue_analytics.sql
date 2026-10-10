-- mart_revenue_analytics: revenue economics by risk and contract segment.
-- Grain: one row per (segment_type, segment_label).
--
-- Revenue lives in the warehouse, not in the app layer: MRR, ARPU, lost
-- MRR (churned customers' monthly charges), realized lifetime value, and
-- expected remaining lifetime value (eCLV) per customer, aggregated up.
--
-- eCLV method (documented, deliberately simple — teachable):
--   With monthly churn probability h, expected remaining lifetime is
--   1/h months (geometric survival), so
--     eCLV = monthly_charges * min(1/h, tenure_cap)   -- cap = 24 months
--   h blends the model's probability with the empirical churn rate of
--   the customer's contract segment:
--     h = 0.5 * churn_probability + 0.5 * contract_churn_rate
--   The cap keeps single-month noise (h = 1.0) from producing silly
--   numbers, and the blend keeps both the model and the data honest.
--   Retention value (addressable eCLV) = eCLV * churn_probability: the
--   revenue expected to walk out the door if nobody intervenes.

with base as (
    select
        m.*,
        p.churn_probability,
        p.risk_band
    from {{ ref('mart_customer_360') }} m
    left join {{ source('ml_outputs', 'churn_predictions') }} p using (customer_id)
),

contract_rate as (
    select contract_label, avg(churned::int) as contract_churn_rate
    from base group by 1
),

per_customer as (
    select
        b.customer_id,
        b.contract_label,
        b.risk_band,
        b.churned,
        b.monthly_charges,
        b.total_charges,
        b.churn_probability,
        greatest(0.02, 0.5 * b.churn_probability + 0.5 * c.contract_churn_rate) as hazard,
        b.monthly_charges
            * least(24.0, 1.0 / greatest(0.02, 0.5 * b.churn_probability
                         + 0.5 * c.contract_churn_rate))                as e_clv
    from base b
    join contract_rate c using (contract_label)
),

segments as (
    select 'risk_band' as segment_type, risk_band as segment_label, 1 as sort_key, *
    from (select distinct risk_band from base where risk_band is not null) t
    union all
    select 'contract' as segment_type, contract_label as segment_label, 2 as sort_key, *
    from (select distinct contract_label from base) t
)

select
    seg.segment_type,
    seg.segment_label,
    count(pc.customer_id)                                          as n_customers,
    count(pc.customer_id) filter (where pc.churned)                as n_churned,
    round(avg(pc.churned::int), 4)                                 as churn_rate,
    round(sum(pc.monthly_charges), 2)                              as mrr,
    round(avg(pc.monthly_charges), 2)                              as arpu,
    round(sum(case when pc.churned then pc.monthly_charges end), 2) as lost_mrr,
    round(sum(case when pc.churned then pc.total_charges end), 2)   as lost_lifetime_value,
    round(avg(pc.e_clv), 2)                                        as avg_e_clv,
    round(sum(pc.e_clv), 2)                                        as total_e_clv,
    -- revenue expected to churn if no intervention: eCLV * hazard share
    round(sum(pc.e_clv * pc.churn_probability), 2)                 as addressable_revenue
from segments seg
left join per_customer pc
    on (seg.segment_type = 'risk_band' and pc.risk_band = seg.segment_label)
    or (seg.segment_type = 'contract' and pc.contract_label = seg.segment_label)
group by seg.segment_type, seg.segment_label, seg.sort_key
order by seg.sort_key, addressable_revenue desc
