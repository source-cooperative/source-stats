# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-06-18

### Added
- **Automatic Cleanup**: Lambda function now automatically removes temporary files after processing
- **Enhanced Logging**: Added cleanup activity logging with 🧹 emojis for visibility
- **Documentation Focus**: Simplified infrastructure folder to focus on understanding vs deployment

### Changed
- **Simplified Directory Structure**: 
  - `account-stats/` → `accounts/`
  - `repository-stats/` → `repositories/`
  - `platform-summary/` → `source/`
- **Streamlined Documentation**: Updated README to focus on what the project is rather than setup instructions
- **Improved Error Handling**: Better permission error messages and troubleshooting

### Fixed
- **File Cleanup**: Resolved temporary file accumulation issues
- **Documentation Accuracy**: Removed outdated claims about features not yet implemented

### Removed
- **Setup Scripts**: Removed deployment-specific infrastructure scripts to focus on project understanding
- **Detailed Setup Instructions**: Simplified approach prioritizing comprehension over step-by-step deployment

## [1.0.0] - 2025-06-18

### Added
- Initial release of Source Stats automation
- Lambda function for automated S3 inventory analysis
- Support for three report types: accounts, repositories, source
- Clean CSV output with proper headers and human-readable filenames (YYYYMMDD.csv)
- Automatic deduplication of inventory records
- Simplified file structure: `[type]/YYYYMMDD.csv`
- IAM policy templates showing required permissions
- Athena table schema documentation
- Basic deployment script for Lambda function updates
- CloudWatch logging integration via standard Python print statements

### Features
- Cost-effective analysis using S3 inventory instead of expensive LIST operations
- Scalable processing via AWS Athena
- Support for petabyte-scale data analysis

### Infrastructure
- IAM policy templates with minimal required permissions
- Athena table configuration examples
- CloudWatch logging integration
- Basic deployment automation script 