-- dim_date: monthly date spine covering the observation window.
--
-- The Telco sample is a Feb-2020 snapshot with no event dates. We anchor
-- tenure backwards from a fixed as-of date (2020-02-01, documented in the
-- README) so every customer's start month can be derived:
--   start_month = as_of - tenure_months
-- The spine spans 2014-02 (72 months back) .. 2020-02 so any start month
-- (tenure 0-72) has a dim_date row.
with months as (
    select range::date as month_start
    from range(
        date '2014-02-01', date '2020-03-01', interval 1 month
    ) t(range)
)

select
    month_start                                 as date_key,        -- first day of month, PK
    year(month_start)                           as year_number,
    month(month_start)                          as month_number,
    year(month_start) * 100 + month(month_start) as yyyymm,
    monthname(month_start)                      as month_name,
    'Q' || quarter(month_start)                 as quarter_label,
    concat(monthname(month_start), ' ', year(month_start)) as month_label
from months
