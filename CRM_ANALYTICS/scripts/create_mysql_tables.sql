-- Connect to MySQL and run this
USE crm_production;

-- Fact table
CREATE TABLE IF NOT EXISTS fact_deals (
    deal_id INT PRIMARY KEY,
    org_id INT,
    pipeline_id INT,
    stage_id INT,
    title VARCHAR(255),
    value DECIMAL(15,2),
    currency VARCHAR(3),
    status VARCHAR(10),
    lost_reason TEXT,
    close_time DATETIME,
    add_time DATETIME,
    won_time DATETIME,
    lost_time DATETIME,
    days_to_close INT,
    won_value DECIMAL(15,2),
    is_won BOOLEAN,
    is_lost BOOLEAN,
    is_open BOOLEAN,
    total_activities INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_add_time (add_time)
);

-- Dimension tables
CREATE TABLE IF NOT EXISTS dim_organization (
    org_id INT PRIMARY KEY,
    org_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_stage (
    stage_id INT PRIMARY KEY,
    stage_name VARCHAR(100),
    order_nr INT,
    pipeline_id INT,
    deal_probability INT,
    days_to_rotten DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_pipeline (
    pipeline_id INT PRIMARY KEY,
    pipeline_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- KPI table
CREATE TABLE IF NOT EXISTS kpi_daily_summary (
    summary_date DATE PRIMARY KEY,
    total_deals INT,
    won_deals INT,
    lost_deals INT,
    revenue_won DECIMAL(15,2),
    win_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Show tables
SHOW TABLES;
