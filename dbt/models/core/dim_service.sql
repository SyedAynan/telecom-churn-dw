-- dim_service: one row per subscribable service (rows, not columns).
--
-- Enumerates the service universe derived from the source columns: phone,
-- internet (two technologies), and the six add-ons. The customer-level
-- subscription flags live in fact_customer_services (the bridge); this
-- dimension just says what CAN be subscribed to.
with services as (
    select * from (values
        ('phone',     'phone_service'),
        ('phone',     'multiple_lines'),
        ('internet',  'internet_dsl'),
        ('internet',  'internet_fiber'),
        ('addon',     'online_security'),
        ('addon',     'online_backup'),
        ('addon',     'device_protection'),
        ('addon',     'tech_support'),
        ('addon',     'streaming_tv'),
        ('addon',     'streaming_movies')
    ) as t(category, service_name)
)

select
    row_number() over (order by category, service_name) as service_key,
    service_name,
    category,
    case service_name
        when 'phone_service'    then 'Phone service'
        when 'internet_dsl'     then 'Internet - DSL'
        when 'internet_fiber'   then 'Internet - Fiber optic'
        when 'multiple_lines'   then 'Multiple lines'
        when 'online_security'  then 'Online security'
        when 'online_backup'    then 'Online backup'
        when 'device_protection' then 'Device protection'
        when 'tech_support'     then 'Tech support'
        when 'streaming_tv'     then 'Streaming TV'
        when 'streaming_movies' then 'Streaming movies'
    end                                                   as service_label,
    case
        when category = 'phone'    then 'Phone'
        when category = 'internet' then 'Internet'
        else 'Add-on'
    end                                                   as category_label
from services
