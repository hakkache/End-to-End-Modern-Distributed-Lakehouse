{{config(materialized='table', tags=['silver'])}}

WITH ticket_enriched AS (

    SELECT
        ticket_id,
        customer_id,
        order_id,
        ticket_type,
        priority,
        status,
        created_timestamp,
        CASE 
            WHEN TRY_CAST(first_response_timestamp AS TIMESTAMP) IS NOT NULL 
            THEN TRY_CAST(first_response_timestamp AS TIMESTAMP)
            ELSE NULL
        END AS first_response_timestamp,
        CASE 
            WHEN TRY_CAST(resolution_timestamp AS TIMESTAMP) IS NOT NULL 
            THEN TRY_CAST(resolution_timestamp AS TIMESTAMP)
            ELSE NULL
        END AS resolution_timestamp,
        agent_id,
        satisfaction_score,
        subject,
        channel,

        CASE 
            WHEN TRY_CAST(first_response_timestamp AS TIMESTAMP) IS NOT NULL THEN 
                DATE_DIFF('minute', created_timestamp, TRY_CAST(first_response_timestamp AS TIMESTAMP))
            ELSE NULL
        END AS first_response_time_minutes,

        CASE 
            WHEN TRY_CAST(resolution_timestamp AS TIMESTAMP) IS NOT NULL THEN 
                DATE_DIFF('hour', created_timestamp, TRY_CAST(resolution_timestamp AS TIMESTAMP))
            ELSE NULL
        END AS resolution_time_hours,

        CASE
            WHEN priority ='urgent' AND TRY_CAST(first_response_timestamp AS TIMESTAMP) IS NOT NULL AND 
                 DATE_DIFF('minute', created_timestamp, TRY_CAST(first_response_timestamp AS TIMESTAMP)) <= 15 THEN TRUE
            WHEN priority ='high' AND TRY_CAST(first_response_timestamp AS TIMESTAMP) IS NOT NULL AND 
                 DATE_DIFF('minute', created_timestamp, TRY_CAST(first_response_timestamp AS TIMESTAMP)) <= 60 THEN TRUE
            WHEN priority ='medium' AND TRY_CAST(first_response_timestamp AS TIMESTAMP) IS NOT NULL AND
                 DATE_DIFF('hour', created_timestamp, TRY_CAST(first_response_timestamp AS TIMESTAMP)) <= 4 THEN TRUE
            WHEN priority ='low' AND TRY_CAST(first_response_timestamp AS TIMESTAMP) IS NOT NULL AND
                 DATE_DIFF('hour', created_timestamp, TRY_CAST(first_response_timestamp AS TIMESTAMP)) <= 24 THEN TRUE
            ELSE FALSE
        END AS meets_response_sla,

        CASE
            WHEN priority ='urgent' AND TRY_CAST(resolution_timestamp AS TIMESTAMP) IS NOT NULL AND 
                 DATE_DIFF('hour', created_timestamp, TRY_CAST(resolution_timestamp AS TIMESTAMP)) <= 4 THEN TRUE
            WHEN priority ='high' AND TRY_CAST(resolution_timestamp AS TIMESTAMP) IS NOT NULL AND 
                 DATE_DIFF('hour', created_timestamp, TRY_CAST(resolution_timestamp AS TIMESTAMP)) <= 24 THEN TRUE
            WHEN priority ='medium' AND TRY_CAST(resolution_timestamp AS TIMESTAMP) IS NOT NULL AND
                 DATE_DIFF('hour', created_timestamp, TRY_CAST(resolution_timestamp AS TIMESTAMP)) <= 72 THEN TRUE
            WHEN priority ='low' AND TRY_CAST(resolution_timestamp AS TIMESTAMP) IS NOT NULL AND
                 DATE_DIFF('hour', created_timestamp, TRY_CAST(resolution_timestamp AS TIMESTAMP)) <= 168 THEN TRUE
            ELSE FALSE
        END AS meets_resolution_sla,

        CASE 
            WHEN status IN ('open','in_progress') THEN 
                DATE_DIFF('hour', created_timestamp, CAST(CURRENT_TIMESTAMP AS TIMESTAMP))
            ELSE NULL
        END AS current_age_hours,

        CASE 
            WHEN satisfaction_score IS NOT NULL AND satisfaction_score >=4 THEN TRUE
            ELSE FALSE
        END AS is_satisfied_customer,

        CASE 
            WHEN satisfaction_score IS NOT NULL AND satisfaction_score <=2 THEN TRUE
            ELSE FALSE
        END AS is_unsatisfied_customer
    
    FROM {{ ref('bronze_support_tickets') }}
),

agent_performance AS (

    SELECT
        agent_id,
        COUNT(*) AS total_tickets_handled,
        AVG(first_response_time_minutes) AS avg_first_response_time_minutes,
        AVG(resolution_time_hours) AS avg_resolution_time_hours,
        COUNT(CASE WHEN meets_resolution_sla THEN 1 END) AS tickets_meeting_sla,
        COUNT(CASE WHEN meets_resolution_sla THEN 1 END) AS tickets_meeting_resolution_sla,
        AVG(satisfaction_score) AS avg_satisfaction_score,
        COUNT(CASE WHEN is_satisfied_customer THEN 1 END) AS satisfied_customers,
        COUNT(CASE WHEN is_unsatisfied_customer THEN 1 END) AS unsatisfied_customers
    
    FROM ticket_enriched
    WHERE agent_id IS NOT NULL
    GROUP BY agent_id
)

SELECT
    t.ticket_id,
    t.customer_id,
    t.order_id,
    t.ticket_type,
    t.priority,
    t.status,
    t.created_timestamp,
    t.first_response_timestamp,
    t.resolution_timestamp,
    t.agent_id,
    t.satisfaction_score,
    t.subject,
    t.channel,
    t.first_response_time_minutes,
    t.resolution_time_hours,
    t.meets_response_sla,
    t.meets_resolution_sla,
    t.current_age_hours,
    t.is_satisfied_customer,
    t.is_unsatisfied_customer,
    
    a.avg_first_response_time_minutes as agent_avg_first_response_time_minutes,
    a.avg_resolution_time_hours as agent_avg_resolution_time_hours,
    a.avg_satisfaction_score as agent_avg_satisfaction_score,

    CASE 
        WHEN t.priority = 'urgent' AND t.current_age_hours > 4 THEN 'Overdue Critical'
        WHEN t.priority = 'high' AND t.current_age_hours > 24 THEN 'Overdue High'
        WHEN t.priority = 'medium' AND t.current_age_hours > 72 THEN 'Overdue Medium'
        WHEN t.priority = 'low' AND t.current_age_hours > 168 THEN 'Overdue Low'
        WHEN t.status IN ('open','in_progress') THEN 'active'
        ELSE 'Resolved'
    END AS ticket_urgency_status,

    CASE 
        WHEN t.channel = 'chat' THEN 'Real-time'
        WHEN t.channel = 'phone' THEN 'Real-time'
        WHEN t.channel = 'email' THEN 'Asynchronous'
        WHEN t.channel = 'social_media' THEN 'Public'
        ELSE 'Other'
    END AS channel_type,

    CURRENT_TIMESTAMP AS processed_at

FROM ticket_enriched t
LEFT JOIN agent_performance a
    ON t.agent_id = a.agent_id