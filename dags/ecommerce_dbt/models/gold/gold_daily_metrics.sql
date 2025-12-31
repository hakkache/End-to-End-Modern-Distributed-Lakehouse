{{ config(materialized='table', tags=['gold']) }}

WITH daily_sessions AS (
    SELECT
       DATE(session_start) as metric_date,
       COUNT(DISTINCT session_id) as total_sessions,
       COUNT(DISTINCT customer_id) as unique_customers,
       AVG(session_duration_seconds) as avg_session_duration_seconds
    
    FROM {{ ref('silver_customer_sessions') }}
    GROUP BY DATE(session_start)
),

daily_payments AS (
    SELECT
        DATE(transaction_timestamp) as metric_date,
        COUNT(*) as total_transactions,
        COUNT(CASE WHEN is_successful THEN 1 END) as successful_transactions,
        SUM(CASE WHEN is_successful THEN amount ELSE 0 END) as daily_revenue,
        AVG(risk_score) as avg_risk_score
    
    FROM {{ ref('silver_payment_analysis') }}
    GROUP BY DATE(transaction_timestamp)
),

daily_support AS (
    SELECT
        DATE(created_timestamp) as metric_date,
        COUNT(*) as total_tickets,
        AVG(first_response_time_minutes/60) as avg_response_time,
        AVG(resolution_time_hours) as avg_resolution_time
    
    FROM {{ ref('silver_support_metrics') }}
    GROUP BY DATE(created_timestamp)
)

SELECT 

    COALESCE(ds.metric_date, dp.metric_date, dsu.metric_date) AS metric_date,

    COALESCE(ds.total_sessions, 0) AS total_sessions,
    COALESCE(ds.unique_customers, 0) AS unique_customers,
    COALESCE(ds.avg_session_duration_seconds, 0) AS avg_session_duration_seconds,

    COALESCE(dp.total_transactions, 0) AS total_transactions,
    COALESCE(dp.successful_transactions, 0) AS successful_transactions,
    COALESCE(dp.daily_revenue, 0) AS daily_revenue,
    COALESCE(dp.avg_risk_score, 0) AS avg_risk_score,

    COALESCE(dsu.total_tickets, 0) AS total_tickets,
    COALESCE(dsu.avg_response_time, 0) AS avg_response_time,
    COALESCE(dsu.avg_resolution_time, 0) AS avg_resolution_time,

    CURRENT_TIMESTAMP AS calculated_at

FROM daily_sessions ds
FULL OUTER JOIN daily_payments dp
    ON ds.metric_date = dp.metric_date
FULL OUTER JOIN daily_support dsu
    ON COALESCE(ds.metric_date, dp.metric_date) = dsu.metric_date