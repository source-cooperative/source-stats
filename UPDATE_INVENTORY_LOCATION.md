# Update Inventory Location

The inventory files have moved from the main Source bucket to `s3://source-inventories`. This requires updating the Athena table location.

## Simple Fix

Run the SQL in `infrastructure/athena-table.sql` to update the table location:

```sql
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
```

## Test

After updating the table, test with:

```bash
AWS_PROFILE=source-stats-deployer python3 test_setup.py
```

## Deploy

Once tested, deploy the Lambda function:

```bash
./deploy.sh
```

That's it! The Lambda function logic remains the same - only the data source location changed. 