{{ config(materialized='table', tags=['bronze']) }}

SELECT
    transaction_id,
    order_id,
    customer_id,
    payment_method,
    payment_status,
    CAST(amount AS DECIMAL(10,2)) AS amount,
    currency,
    CAST(transaction_timestamp AS TIMESTAMP) AS transaction_timestamp,
    CAST(processor_response_code AS VARCHAR) AS processor_response_code,
    CAST(gateway_fee AS DECIMAL(10,2)) AS gateway_fee,
    merchant_id,
    billing_country,
    risk_score,
    CURRENT_TIMESTAMP AS ingested_at,
    'payment_transactions' AS source_system
FROM {{ ref('payment_transactions') }}
--WHERE transaction_id IS NOT NULL
    --AND order_id IS NOT NULL
    --AND transaction_timestamp IS NOT NULL