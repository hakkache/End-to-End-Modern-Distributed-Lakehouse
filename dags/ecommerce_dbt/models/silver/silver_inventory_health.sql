{{ config(materialized='table', tags=['silver']) }}

WITH latest_inventory AS (

    SELECT
        product_id,
        warehouse_id,
        snapshot_date,
        quantity_on_hand,
        quantity_reserved,
        quantity_available,
        reorder_point,
        reorder_quantity,
        supplier_id,
        unit_cost,
        ROW_NUMBER() OVER (PARTITION BY product_id, warehouse_id ORDER BY snapshot_date DESC, ingested_at DESC) AS rn
    FROM {{ ref('bronze_inventory_snapshots') }}
),

inventory_metrics AS (

    SELECT
        product_id,
        warehouse_id,
        snapshot_date,
        quantity_on_hand,
        quantity_reserved,
        quantity_available,
        reorder_point,
        reorder_quantity,
        supplier_id,
        unit_cost,

        CASE
            WHEN quantity_available <= 0 THEN 'out of stock'
            WHEN quantity_available <= reorder_point THEN 'low stock'
            WHEN quantity_available <= reorder_point*2 THEN 'Medium stock'
            ELSE 'High stock'
        END AS stock_status,


        CASE 
            WHEN quantity_available > 0 THEN
                CAST(quantity_available AS DOUBLE) / GREATEST(1, reorder_point)*30
            ELSE NULL
        END AS estimated_days_of_inventory,


        CASE 
            WHEN quantity_available <= reorder_point THEN TRUE
            ELSE FALSE
        END AS needs_reorder,

        CASE 
            WHEN quantity_on_hand > 0 THEN
                CAST(reorder_quantity AS DOUBLE) / quantity_on_hand*12
            ELSE 0
        END AS estimated_annual_turns,


        quantity_on_hand*unit_cost AS inventory_value,
        quantity_available*unit_cost AS available_inventory_value

    FROM latest_inventory
    WHERE rn = 1)

SELECT
    product_id,
    warehouse_id,
    snapshot_date,
    quantity_on_hand,
    quantity_reserved,
    quantity_available,
    reorder_point,
    reorder_quantity,
    supplier_id,
    unit_cost,
    stock_status,
    estimated_days_of_inventory,
    needs_reorder,
    estimated_annual_turns,
    inventory_value,
    available_inventory_value,
    CASE 
        WHEN stock_status = 'out of stock' THEN 'critical'
        WHEN stock_status = 'low stock' AND estimated_days_of_inventory < 7 THEN 'high'
        WHEN stock_status = 'low stock' THEN 'medium'
        ELSE 'low'
    END AS inventory_risk_level,
    CURRENT_TIMESTAMP AS processed_at

FROM inventory_metrics