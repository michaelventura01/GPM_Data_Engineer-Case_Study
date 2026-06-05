{{ config(materialized='table') }}

SELECT 
    -- Map columns dynamically
    ID,
    Title,
    Value,
    "Org ID" AS Org_ID,  -- Handle spaces in column names
    "Stage ID" AS Stage_ID,
    Currency,
    "Add time"::TIMESTAMP AS Add_time,
    "Update time"::TIMESTAMP AS Update_time,
    Status,
    "Lost reason" AS Lost_reason,
    "Close time"::TIMESTAMP AS Close_time,
    "Pipeline ID" AS Pipeline_ID,
    "Won time"::TIMESTAMP AS Won_time,
    "Lost time"::TIMESTAMP AS Lost_time,
    "Stage change time"::TIMESTAMP AS Stage_change_time,
    "Is deleted" AS Is_deleted,
    
    -- Derived columns
    CASE 
        WHEN Value = 0 THEN 'Lead_Generation'
        WHEN Value > 0 AND Value <= 1000 THEN 'Small'
        WHEN Value > 1000 AND Value <= 5000 THEN 'Medium'
        WHEN Value > 5000 AND Value <= 15000 THEN 'Large'
        ELSE 'Enterprise'
    END AS value_bucket,
    
    CASE WHEN Status = 'won' THEN 1 ELSE 0 END AS is_won
    
FROM {{ source('crm', 'deals_raw') }}
WHERE "Is deleted" = FALSE OR "Is deleted" IS NULL