# Source Stats

AWS Lambda function that automatically analyzes Source Cooperative's S3 inventory data using Athena and generates clean CSV reports. The analysis performed by this Lambda function relies on the [account_id]/[repository_id] prefix structure used by Source. Note that this does not perform any analysis of Source Data products that are hosted in Microsoft Azure.

## Overview

This Lambda function generates three types of reports:

- **Account Statistics** (`accounts/`): Storage and object counts per account
- **Repository Statistics** (`repositories/`): Detailed breakdown per repository 
- **Source Summary** (`source/`): High-level platform metrics

## How It Works

1. **S3 Inventory** generates weekly reports Source data
2. **Athena Table** provides SQL access to the inventory data  
3. **Lambda Function** runs Athena queries and generates clean CSV reports that are published to Source Cooperative at [source/source-stats](https://source.coop/source/source-stats)

## Prerequisites

- AWS Account with appropriate permissions
- S3 bucket with inventory configuration enabled
- Athena database and workgroup configured
- Lambda execution role with required permissions

## Configuration

The Lambda function is pre-configured for Source Cooperative's environment:

```python
results_bucket = 'us-west-2.opendata.source.coop'
results_prefix = 'source/source-stats/'
database = 'source_stats'
workgroup = 'primary'
```

For custom deployments, update these variables in `lambda_function.py`:

- `results_bucket` - S3 bucket for output files
- `results_prefix` - Path prefix for reports  
- `database` - Athena database name
- `workgroup` - Athena workgroup

### Required IAM Permissions

The Lambda execution role needs:
- **S3**: Read/write access to results bucket and temp directories
- **Athena**: Query execution permissions
- **Glue**: Catalog access for database metadata
- **CloudWatch**: Logging permissions

See `infrastructure/source-stats-deployment-policy.json` for the complete policy.

## Output Format

### File Structure
```
s3://us-west-2.opendata.source.coop/source/source-stats/
├── accounts/source-stats-accounts-20250618.csv      # Account-level statistics
├── repositories/source-stats-repositories-20250618.csv  # Repository-level details
└── source/source-stats-summary-20250618.csv        # Platform summary metrics
```

### Sample Output

**accounts/20250618.csv**:
```csv
account,repositories,objects,storage_gb,avg_object_size_mb,oldest_file,newest_file
earthgenome,4,1324538,190595.3,147.35,2024-04-17 18:11:22,2025-04-17 12:23:46
dynamical,6,2669469,167029.21,64.07,2024-07-02 03:28:29,2025-06-15 00:17:07
```

**source/20250618.csv**:
```csv
metric,value
Total Accounts,77
Total Repositories,313
Total Objects,85891033
Total Storage (TB),747.3
```

## Automation

### EventBridge Scheduling

Set up automatic execution with EventBridge:

```bash
# Create rule for daily execution at 6 AM UTC
aws events put-rule \
    --name s3-inventory-daily \
    --schedule-expression "cron(0 6 * * ? *)"

# Add Lambda target
aws events put-targets \
    --rule s3-inventory-daily \
    --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:source-stats"
```

### Trigger on Inventory Completion

Trigger automatically when new inventory is available:

```bash
aws events put-rule \
    --name s3-inventory-trigger \
    --event-pattern '{"source":["aws.s3"],"detail-type":["S3 Inventory Report Available"]}'
```

## Monitoring

Monitor the Lambda function via CloudWatch metrics (duration, errors, invocations) and check the `/aws/lambda/source-stats` log group for execution details.

## Cost Optimization

- **S3 Inventory**: Uses S3 inventory instead of expensive LIST operations
- **Automatic Cleanup**: Removes temporary files (`temp/`, `athena-temp/`) after each run
- **Deduplication**: Uses `DISTINCT` to handle duplicate inventory records efficiently
- **Minimal Permissions**: IAM policies restricted to specific S3 prefixes only

### Automatic Cleanup Process

The Lambda function automatically cleans up temporary directories after processing:

1. **Athena Temp Files**: Query result files in `athena-temp/` directory
2. **Processing Temp Files**: Intermediate files in `temp/` directory  
3. **Logging**: Shows cleanup activity in CloudWatch logs (`🧹 Cleaned up X files`)

This prevents accumulation of temporary files and reduces storage costs.

## Troubleshooting

### Common Issues

**Query Timeout**:
- Increase Lambda timeout (max 15 minutes)
- Optimize Athena queries
- Check workgroup configuration

**Permission Errors**:
- Verify Lambda execution role has `SourceStatsLambdaExecutionPolicy` attached
- Check S3 bucket policies allow access to `source/source-stats/*` prefix
- Ensure Athena database access and Glue catalog permissions
- Verify temp directory permissions (`source/source-stats/temp/*`)

**Missing Data**:
- Verify inventory configuration
- Check table location path
- Confirm data availability

### Debug Mode

Enable detailed logging by setting CloudWatch log level to DEBUG in Lambda configuration.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 🐛 **Bug Reports**: [Create an issue](https://github.com/source-cooperative/source-stats/issues)
- 💬 **Questions**: [Source Cooperative Slack](https://join.slack.com/t/sourcecoop/shared_invite/zt-212sakf1j-fONCD4lZ_v2HP2PDpTr2dw) 

aws iam put-role-policy \
     --role-name arn:aws:iam::417712557820:role/source-stats-lambda-role \
     --policy-name SourceStatsLambdaPolicy \
     --policy-document file://infrastructure/iam-policy.json \
     --profile source-stats-deployer