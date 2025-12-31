{{ config(materialized='table', tags=['silver']) }}

WITH payment_enriched AS (

    SELECT
        transaction_id,
        order_id,
        customer_id,
        payment_method,
        payment_status,
        amount,
        currency,
        transaction_timestamp,
        processor_response_code,
        gateway_fee,
        merchant_id,
        billing_country,
        risk_score,

        EXTRACT(HOUR FROM transaction_timestamp) AS transaction_hour,
        EXTRACT(DOW FROM transaction_timestamp) AS transaction_day_of_week,
        DATE(transaction_timestamp) AS transaction_date,

        CASE
            WHEN payment_status = 'completed' THEN TRUE
            ELSE FALSE
        END AS is_successful,

        CASE
            WHEN risk_score >= 80 THEN TRUE
            ELSE FALSE
        END AS is_high_risk,

        CASE
            WHEN payment_status ='failed' THEN TRUE
            ELSE FALSE
        END AS is_failed,

        CASE 
            WHEN payment_status = 'refunded' THEN TRUE
            ELSE FALSE
        END AS is_refunded,

        amount - gateway_fee AS net_amount
    
    FROM {{ ref('bronze_payment_transactions') }}
),

customer_payment_patterns AS (

    SELECT 
        customer_id,
        COUNT(*) AS total_transactions,
        COUNT(CASE WHEN is_successful THEN 1 END) AS successful_transactions,
        COUNT(CASE WHEN is_failed THEN 1 END) AS failed_transactions,
        COUNT(CASE WHEN is_high_risk THEN 1 END) AS high_risk_transactions,
        AVG(amount) AS avg_transaction_amount,
        MAX(amount) AS max_transaction_amount,
        SUM(CASE WHEN is_successful THEN amount ELSE 0 END) AS total_sucessful_amount,
        COUNT(DISTINCT payment_method) AS unique_payment_methods
    
    FROM payment_enriched
    GROUP BY customer_id
)

SELECT
    p.transaction_id,
    p.order_id,
    p.customer_id,
    p.payment_method,
    p.payment_status,
    p.amount,
    p.currency,
    p.transaction_timestamp,
    p.transaction_hour,
    p.transaction_day_of_week,
    p.transaction_date,
    p.processor_response_code,
    p.gateway_fee,
    p.net_amount,
    p.merchant_id,
    p.billing_country,
    p.risk_score,
    p.is_successful,
    p.is_high_risk,
    p.is_failed,
    p.is_refunded,

    cp.total_transactions as customer_total_transactions,
    cp.successful_transactions as customer_successful_transactions,
    cp.failed_transactions as customer_failed_transactions,
    cp.avg_transaction_amount as customer_avg_transaction_amount,
    cp.max_transaction_amount as customer_max_transaction_amount,

    CASE 
        WHEN CAST(cp.failed_transactions AS DOUBLE) / NULLIF(cp.total_transactions,0) > 0.3 THEN TRUE
        ELSE FALSE
    END AS is_high_failure_rate_customer,

    CASE 
        WHEN p.amount > cp.avg_transaction_amount *3 THEN TRUE
        ELSE FALSE
    END AS is_unusual_large_transaction,
    CASE
        WHEN p.payment_method  IN ('credit_card', 'debit_card') THEN 'low_risk'
        WHEN p.payment_method IN ('paypal', 'apple_pay', 'google_pay') THEN 'medium_risk'
        ELSE 'high_risk'
    END AS payment_method_risk_category,
    CURRENT_TIMESTAMP AS processed_at

FROM payment_enriched p
LEFT JOIN customer_payment_patterns cp
    ON p.customer_id = cp.customer_id