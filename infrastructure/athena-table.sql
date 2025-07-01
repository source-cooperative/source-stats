-- Update Athena table location for S3 inventory data
-- Simple location update to use source-inventories bucket

-- Drop and recreate with new location
DROP TABLE IF EXISTS source_stats.inventory_data;

CREATE EXTERNAL TABLE source_stats.inventory_data (
    bucket string,
    key string,
    size bigint,
    last_modified_date timestamp,
    checksum_algorithm string
)
STORED AS PARQUET
LOCATION 's3://source-inventories/us-west-2.opendata.source.coop/us-west-2.opendata.source.coop-inventory/data/'; 