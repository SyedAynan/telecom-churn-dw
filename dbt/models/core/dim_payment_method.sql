-- dim_payment_method: one row per payment method (4 rows).
-- Grain: payment_method (natural key, lowercased in staging).
with distinct_payments as (
    select distinct payment_method
    from {{ ref('stg_telco_churn') }}
)

select
    payment_method                       as payment_method_key,
    case payment_method
        when 'electronic check'          then 'Electronic check'
        when 'mailed check'              then 'Mailed check'
        when 'bank transfer (automatic)' then 'Bank transfer (automatic)'
        when 'credit card (automatic)'   then 'Credit card (automatic)'
    end                                  as payment_method_label,
    contains(payment_method, 'automatic') as is_automatic,
    case
        when contains(payment_method, 'automatic') then 'Automatic'
        else 'Manual'
    end                                  as payment_automation
from distinct_payments
