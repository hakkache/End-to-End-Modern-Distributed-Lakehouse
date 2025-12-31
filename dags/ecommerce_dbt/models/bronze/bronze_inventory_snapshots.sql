{{ config(materialized='table', tags=['bronze']) }}

SELECT
    snapshot_id,
    product_id,
    warehouse_id,
    CAST(snapshot_date AS DATE) AS snapshot_date,
    CAST(quantity_on_hand AS INTEGER) AS quantity_on_hand,
    CAST(quantity_reserved AS INTEGER) AS quantity_reserved,
    CAST(quantity_available AS INTEGER) AS quantity_available,
    CAST(reorder_point AS INTEGER) AS reorder_point,
    CAST(reorder_quantity AS INTEGER) AS reorder_quantity,
    supplier_id,
    CAST(last_received_date AS DATE) AS last_received_date,
    CAST(unit_cost AS DECIMAL(10,2)) AS unit_cost,
    CURRENT_TIMESTAMP AS ingested_at,
    'inventory_snapshots' AS source_system
FROM {{ ref('inventory_snapshots') }}
--WHERE snapshot_id IS NOT NULL
    --AND product_id IS NOT NULL
    --AND snapshot_date IS NOT NULL