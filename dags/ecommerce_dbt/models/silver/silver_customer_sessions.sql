{{ config(materialized='table', tags=['silver']) }}

WITH session_events AS (

    SELECT 
        customer_id,
        session_id,
        MIN(event_timestamp) AS session_start,
        MAX(event_timestamp) AS session_end,
        COUNT(*) AS total_events,
        COUNT(DISTINCT event_type) AS unique_event_types,
        COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) AS page_views,
        COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) AS product_views,
        COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) AS cart_adds,
        COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) AS purchases,
        COUNT(DISTINCT product_id) AS unique_products_viewed,
        device_type,
        referrer_source
    FROM {{ ref('bronze_customer_events') }}
    GROUP BY customer_id, session_id, device_type, referrer_source
),

session_metrics as (

    SELECT
        *,
        DATE_DIFF('second', session_start, session_end) AS session_duration_seconds,
        CASE
            WHEN purchases > 0 THEN TRUE
            ELSE FALSE
        END AS converted,

        CASE 
            WHEN cart_adds > 0 AND purchases = 0 THEN TRUE
            ELSE FALSE
        END as abandoned_cart,

        CASE 
            WHEN total_events = 1 THEN TRUE
            ELSE FALSE
        END as bounce_session
    
    FROM session_events
)

SELECT
    customer_id,
    session_id,
    session_start,
    session_end,
    session_duration_seconds,
    CASE 
        WHEN session_duration_seconds < 30 THEN 'very_short'
        WHEN session_duration_seconds < 300 THEN 'short'
        WHEN session_duration_seconds < 1800 THEN 'Medimum'
        ELSE 'long'
    END AS session_length_category,
    total_events,
    unique_event_types,
    page_views,
    product_views,
    cart_adds,
    purchases,
    unique_products_viewed,
    converted,
    abandoned_cart,
    bounce_session,
    device_type,
    referrer_source,
    CURRENT_TIMESTAMP AS processed_at

FROM session_metrics