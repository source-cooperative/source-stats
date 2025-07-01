# EventBridge Automation Setup - Next Steps

## Current State Summary (as of June 30, 2025)

### ✅ Completed Work
- **S3 Inventory Migration**: Successfully migrated from `s3://us-west-2.opendata.source.coop` to `s3://source-inventories`
- **Athena Table**: Updated to point to new location `s3://source-inventories/us-west-2.opendata.source.coop/us-west-2.opendata.source.coop-inventory/data/`
- **Lambda Function**: Updated to use inventory date `250629` (June 29, 2025) instead of current date
- **File Naming**: Changed from YYYYMMDD to YYMMDD format
- **Temp File Management**: All temp files now go to `s3://source-inventories/temp/` keeping main bucket clean
- **Permissions**: Updated IAM policies and bucket policies for cross-bucket access
- **Testing**: All systems tested and working correctly

### 📂 Current Output Files
```
s3://us-west-2.opendata.source.coop/source/source-stats/
├── README.md
├── accounts/source-stats-accounts-250629.csv
├── repositories/source-stats-repositories-250629.csv
└── source/source-stats-summary-250629.csv
```

### 📅 Inventory Schedule
- S3 inventory runs **weekly** at 01:00 UTC
- Recent inventory dates: June 18, June 22, **June 29** (current)
- Next expected: July 6, 2025

## 🎯 Next Task: EventBridge Automation

### Goal
Set up automated triggers so the Lambda function runs when new S3 inventory data is available.

### Three Automation Options

#### Option 1: S3 Event Notification (Recommended)
- **Trigger**: S3 event when new `manifest.json` created in `s3://source-inventories`
- **Path**: `us-west-2.opendata.source.coop/us-west-2.opendata.source.coop-inventory/YYYY-MM-DDTHH-MMZ/manifest.json`
- **Pros**: Event-driven, immediate processing
- **Cons**: Need to modify Lambda to auto-detect latest date

#### Option 2: Scheduled EventBridge Rule
- **Trigger**: Weekly schedule (e.g., every Sunday at 02:00 UTC)
- **Pros**: Simple, predictable
- **Cons**: Fixed schedule, might run before inventory completes

#### Option 3: Hybrid (Best)
- **Trigger**: S3 event notifications
- **Enhancement**: Add auto-date detection back to Lambda
- **Pros**: Event-driven + automatically uses correct date

### Required Changes for Full Automation

1. **Restore Dynamic Date Detection**: 
   - Remove hardcoded `date_str = '250629'`
   - Add back the `get_latest_inventory_date()` function (fix scoping issues)
   - Or detect date from S3 event payload

2. **Set up EventBridge Rule**:
   - Create rule to listen for S3 events
   - Configure target as Lambda function
   - Set appropriate filters for manifest.json files

3. **Update IAM Permissions**:
   - Add EventBridge permissions to Lambda role
   - Add S3 event notification permissions

### Commands to Start Next Session

```bash
cd /Users/jed/ref-github/source-stats
git log --oneline -5  # See recent commits
git status            # Check current state
./test_setup.py       # Verify everything still works
```

### Key Files Modified
- `lambda_function.py` - Main logic (currently uses hardcoded date)
- `infrastructure/iam-policy.json` - Lambda permissions
- `source-inventories-bucket-policy.json` - Cross-bucket access
- `test_setup.py` - Testing script

### Configuration Details
- **Lambda Function**: `source-stats` (us-west-2)
- **Athena Database**: `source_stats`
- **Athena Table**: `inventory_data`
- **Profile**: `source-stats-deployer`
- **Test Profile**: `source-coop-readonly`

### Current Data Statistics
- **Records**: 217M+ objects
- **Storage**: 1.6+ TB
- **Top Accounts**: earthgenome, dynamical, cworthy, priyald17

---

**Ready for EventBridge automation setup!** 🚀 