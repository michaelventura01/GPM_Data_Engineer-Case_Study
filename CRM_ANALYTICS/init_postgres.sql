-- Create schemas
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dbt_transformations;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Staging tables
CREATE TABLE IF NOT EXISTS staging.deals_raw (
    ID INTEGER,
    Title VARCHAR(255),
    Value DECIMAL(15,2),
    Org_ID INTEGER,
    Stage_ID INTEGER,
    Currency VARCHAR(3),
    Add_time TIMESTAMP,
    Update_time TIMESTAMP,
    Status VARCHAR(10),
    Lost_reason TEXT,
    Close_time TIMESTAMP,
    Pipeline_ID INTEGER,
    Won_time TIMESTAMP,
    Lost_time TIMESTAMP,
    Stage_change_time TIMESTAMP,
    Is_deleted BOOLEAN,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.activities_raw (
    ID INTEGER,
    Subject VARCHAR(100),
    Is_deleted BOOLEAN,
    Add_time TIMESTAMP,
    Update_time TIMESTAMP,
    Deal_ID INTEGER,
    Org_ID INTEGER,
    Done BOOLEAN,
    Marked_as_done_time TIMESTAMP,
    Due_Datetime TIMESTAMP,
    Duration_Hours DECIMAL(10,2),
    Duration_Minutes INTEGER,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.stages_raw (
    ID INTEGER,
    Name VARCHAR(100),
    Order_nr INTEGER,
    Pipeline_ID INTEGER,
    Deal_probability INTEGER,
    Days_to_rotten DECIMAL(10,2),
    Is_deleted BOOLEAN,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.pipeline_raw (
    ID INTEGER,
    Name VARCHAR(100),
    Is_deleted BOOLEAN,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.organizations_raw (
    ID INTEGER,
    Name VARCHAR(255),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

GRANT ALL ON SCHEMA staging TO staging_user;
GRANT ALL ON SCHEMA dbt_transformations TO staging_user;
GRANT ALL ON SCHEMA intermediate TO staging_user;
EOF

# Create MySQL init script
cat > init_mysql.sql << 'EOF'
CREATE DATABASE IF NOT EXISTS crm_production;
USE crm_production;

CREATE TABLE IF NOT EXISTS fact_deals (
    deal_id INT PRIMARY KEY,
    org_id INT,
    pipeline_id INT,
    stage_id INT,
    value DECIMAL(15,2),
    status VARCHAR(10),
    days_to_close INT,
    add_time DATETIME,
    weighted_value DECIMAL(15,2),
    is_won BOOLEAN,
    total_activities INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

GRANT ALL PRIVILEGES ON crm_production.* TO 'prod_user'@'%';
FLUSH PRIVILEGES;