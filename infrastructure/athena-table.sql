-- Create Athena table for S3 inventory data
-- Update the LOCATION with your S3 inventory path

CREATE EXTERNAL TABLE source_stats.inventory_data (
    bucket string,
    key string,
    size bigint,
    last_modified_date timestamp,
    checksum_algorithm string
)
STORED AS PARQUET
LOCATION 's3://YOUR-BUCKET/path/to/inventory/data/'
TBLPROPERTIES (
    'projection.enabled' = 'true',
    'projection.dt.type' = 'date',
    'projection.dt.range' = '2024/01/01,NOW',
    'projection.dt.format' = 'yyyy/MM/dd',
    'storage.location.template' = 's3://YOUR-BUCKET/path/to/inventory/data/${dt}/'
); 