-- Staging model: cleaned + typed one-to-one view of raw.telco_churn.
-- Grain: one row per customer (customer_id).
-- Layer contract: rename to snake_case, standardize categoricals to
-- lowercase, type numerics. Business rules (e.g. total_charges imputation)
-- live here too — the only place they're allowed to.

with source as (
    select * from {{ source('raw', 'telco_churn') }}
),

typed as (
    select
        cast(customerID as varchar)                          as customer_id,
        lower(trim(gender))                                  as gender,           -- 'male' / 'female'
        cast(SeniorCitizen as integer)                       as senior_citizen,   -- 0/1
        lower(Partner)                                       as has_partner,      -- yes/no
        lower(Dependents)                                    as has_dependents,   -- yes/no
        cast(tenure as integer)                              as tenure_months,
        lower(PhoneService)                                  as phone_service,    -- yes/no
        lower(trim(MultipleLines))                           as multiple_lines,   -- yes/no/'no phone service'
        lower(trim(InternetService))                         as internet_service, -- dsl/fiber optic/no
        lower(trim(OnlineSecurity))                          as online_security,
        lower(trim(OnlineBackup))                            as online_backup,
        lower(trim(DeviceProtection))                        as device_protection,
        lower(trim(TechSupport))                             as tech_support,
        lower(trim(StreamingTV))                             as streaming_tv,
        lower(trim(StreamingMovies))                         as streaming_movies,
        lower(trim(Contract))                                as contract_type,    -- month-to-month/one year/two year
        lower(PaperlessBilling)                              as paperless_billing,
        lower(trim(PaymentMethod))                           as payment_method,
        cast(MonthlyCharges as double)                       as monthly_charges,
        -- business rule: tenure-0 customers have blank TotalCharges in the
        -- source -> 0.0 (no tenure yet, no charges yet). Guarded by the
        -- assert_total_charges_not_null singular test.
        case when cast(tenure as integer) = 0 then 0.0
             else cast(TotalCharges as double) end           as total_charges,
        lower(Churn)                                         as churned           -- yes/no
    from source
)

select * from typed
