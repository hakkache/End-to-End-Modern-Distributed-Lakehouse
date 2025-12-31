{{config(materialized='table',tags=['bronze'])}}

SELECT
    event_id,
    customer_id,
    session_id,
    event_type,
    CAST(event_timestamp AS TIMESTAMP) AS event_timestamp,
    page_url,
    NULLIF(product_id, '') AS product_id,
    NULLIF(category_id, '') AS category_id,
    referrer_source,
    device_type,
    user_agent,
    ip_address,
    CURRENT_TIMESTAMP AS ingested_at,
    'customer_events' AS source_system
FROM {{ ref('customer_events') }}
--WHERE event_id IS NOT NULL
    --AND customer_id IS NOT NULL
    --AND event_timestamp IS NOT NULL
 