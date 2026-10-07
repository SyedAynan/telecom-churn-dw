-- dim_contract: one row per contract type.
-- Grain: contract_type (natural key, used as PK to keep the mini-project simple).
with distinct_contracts as (
    select distinct contract_type
    from {{ ref('stg_telco_churn') }}
)

select
    contract_type                      as contract_key,
    case contract_type
        when 'month-to-month' then 'Month-to-month'
        when 'one year'       then 'One year'
        when 'two year'       then 'Two year'
    end                                as contract_label,
    case contract_type
        when 'month-to-month' then 1
        when 'one year'       then 12
        when 'two year'       then 24
    end                                as contract_months,
    case contract_type
        when 'month-to-month' then true
        else false
    end                                as is_flexible
from distinct_contracts
