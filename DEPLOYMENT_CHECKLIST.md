# Deployment Checklist

## ✅ Completed
- [x] Updated Lambda function with YYMMDD date format
- [x] Changed temp storage to use `s3://source-inventories`
- [x] Updated Athena table to point to new inventory location
- [x] Deployed Lambda function code

## 🔧 Manual Steps Required

### 1. Update Lambda IAM Permissions

The Lambda execution role needs access to the `source-inventories` bucket. Update the role policy with the content from `infrastructure/iam-policy.json`:

```bash
# Find the Lambda execution role name
aws lambda get-function --function-name source-stats --region us-west-2 --profile source-stats-deployer --query 'Configuration.Role'

# Update the role policy (replace ROLE-NAME with actual role name)
aws iam put-role-policy \
  --role-name ROLE-NAME \
  --policy-name SourceStatsLambdaPolicy \
  --policy-document file://infrastructure/iam-policy.json \
  --profile source-stats-deployer
```

### 2. Test After IAM Update

```bash
AWS_PROFILE=source-stats-deployer python3 test_setup.py
AWS_PROFILE=source-stats-deployer aws lambda invoke --function-name source-stats --region us-west-2 response.json
```

Expected output files with new naming:
- `accounts/source-stats-accounts-250701.csv`
- `repositories/source-stats-repositories-250701.csv`
- `source/source-stats-summary-250701.csv`

## 📊 Inventory Configuration for Other Buckets

Based on the account scan, these buckets contain data that would benefit from inventory:

### Priority Buckets (Have Data)
1. **`radiant-mlhub`** - ML Hub datasets (many collections)
2. **`us-east-1.opendata.source.coop`** - Regional Source data
3. **`nasa-iserv`** - NASA ISS Earth observation data

### Regional Source Buckets (Check if they have data)
- `ap-northeast-2.opendata.source.coop`
- `ap-northeast-3.opendata.source.coop`
- `ap-south-1.opendata.source.coop`
- `ap-southeast-1.opendata.source.coop`
- `ap-southeast-2.opendata.source.coop`
- `ca-central-1.opendata.source.coop`
- `eu-central-1.opendata.source.coop`
- `eu-north-1.opendata.source.coop`
- `eu-west-1.opendata.source.coop`
- `eu-west-2.opendata.source.coop`
- `eu-west-3.opendata.source.coop`
- `sa-east-1.opendata.source.coop`
- `tokyo.opendata.source.coop`
- `us-east-2.opendata.source.coop`
- `us-west-1.opendata.source.coop`

### Inventory Configuration Template

For each bucket that should have inventory enabled:

1. **Enable S3 Inventory** (via Console or CLI)
   - **Destination bucket**: `source-inventories`
   - **Destination prefix**: `{bucket-name}/`
   - **Format**: Parquet
   - **Frequency**: Daily
   - **Include versions**: Current only
   - **Optional fields**: Size, LastModifiedDate, StorageClass, ETag

2. **CLI Example** (replace `BUCKET-NAME`):
```bash
aws s3api put-bucket-inventory-configuration \
  --bucket BUCKET-NAME \
  --id daily-inventory \
  --inventory-configuration '{
    "Id": "daily-inventory",
    "IsEnabled": true,
    "Destination": {
      "S3BucketDestination": {
        "Bucket": "arn:aws:s3:::source-inventories",
        "Prefix": "BUCKET-NAME/",
        "Format": "Parquet"
      }
    },
    "Schedule": {
      "Frequency": "Daily"
    },
    "IncludedObjectVersions": "Current",
    "OptionalFields": ["Size", "LastModifiedDate", "StorageClass", "ETag"]
  }'
```

### 3. Update Source Stats for Multi-Bucket Analysis

Once multiple buckets have inventory configured, the Lambda function could be enhanced to:

1. **Auto-discover** inventory data in `s3://source-inventories/`
2. **Aggregate stats** across all buckets
3. **Create combined reports** showing global Source Cooperative usage

## 🔍 Next Steps

1. Apply IAM policy updates
2. Test Lambda function 
3. Configure inventory for priority buckets (`radiant-mlhub`, `us-east-1.opendata.source.coop`)
4. Monitor inventory data arrival (takes 24-48 hours for first reports)
5. Consider enhancing Lambda for multi-bucket analysis 