{{ config(materialized='table', tags=['gold']) }}

WITH product_events AS (

    SELECT
      product_id,
      COUNT(*) AS total_events,
      COUNT(DISTINCT customer_id) AS unique_customers,
      COUNT(DISTINCT session_id) AS total_sessions
    
    FROM {{ ref('bronze_customer_events') }}
    WHERE product_id IS NOT NULL
    GROUP BY product_id
),

product_inventory AS (

    SELECT
        product_id,
        AVG(quantity_on_hand) AS avg_quantity_on_hand,
        AVG(reorder_point) AS avg_reorder_point,
        MAX(needs_reorder) AS needs_reorder
    FROM {{ ref('silver_inventory_health') }}
    GROUP BY product_id

)

SELECT
    COALESCE(pe.product_id, pi.product_id) AS product_id,
    COALESCE(pe.unique_customers, 0) AS unique_customers,
    COALESCE(pe.total_sessions, 0) AS total_sessions,

    COALESCE(pi.avg_quantity_on_hand, 0) AS avg_quantity_on_hand,
    COALESCE(pi.avg_reorder_point, 0) AS avg_reorder_point,
    COALESCE(pi.needs_reorder, FALSE) AS needs_reorder,
    CURRENT_TIMESTAMP AS calculated_at

FROM product_events pe
FULL OUTER JOIN product_inventory pi
    ON pe.product_id = pi.product_id