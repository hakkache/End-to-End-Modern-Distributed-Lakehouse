{{ config(materialized='table', tags=['bronze']) }}

SELECT
    ticket_id,
    customer_id,
    NULLIF(CAST(order_id AS VARCHAR), '') as order_id,
    ticket_type,
    priority,
    status,
    CAST(created_timestamp AS TIMESTAMP) AS created_timestamp,
    CASE 
        WHEN first_response_timestamp IS NULL OR CAST(first_response_timestamp AS VARCHAR) = '' THEN NULL
        ELSE CAST(first_response_timestamp AS TIMESTAMP) END AS first_response_timestamp,
    CASE 
        WHEN resolution_timestamp IS NULL OR CAST(resolution_timestamp AS VARCHAR) = '' THEN NULL
        ELSE CAST(resolution_timestamp AS TIMESTAMP) END AS resolution_timestamp,
    agent_id,
    CAST(NULLIF(CAST(satisfaction_score AS VARCHAR), '') AS INTEGER) AS satisfaction_score,
    subject,
    channel,
    CURRENT_TIMESTAMP AS ingested_at,
    'support_tickets' AS source_system
FROM {{ ref('support_tickets') }}
--WHERE ticket_id IS NOT NULL
    --AND customer_id IS NOT NULL
    --AND created_timestamp IS NOT NULL
