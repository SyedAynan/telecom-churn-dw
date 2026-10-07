{# Baseline model contracts: at least one test per column's grain rules,
   plus a generic helper so marts can reuse the same rule expression. #}
{% test no_blank_ids(model, column_name) %}

select * from {{ model }} where {{ column_name }} is null or trim({{ column_name }}) = ''

{% endtest %}
