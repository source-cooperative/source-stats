#!/bin/bash
set -e

# Source Stats Lambda Deployment Script
# Update these variables for your AWS environment

FUNCTION_NAME="source-stats"
AWS_REGION="us-west-2"
AWS_PROFILE="source-stats-deployer"

echo "🚀 Deploying Source Stats Lambda Function"

# Create deployment package
echo "📦 Creating deployment package..."
zip -r lambda_function.zip lambda_function.py

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $AWS_REGION --profile $AWS_PROFILE 2>/dev/null; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda_function.zip \
        --region $AWS_REGION \
        --profile $AWS_PROFILE
else
    echo "➕ Creating new Lambda function..."
    echo "⚠️  Please create the Lambda function manually first with appropriate IAM role"
    echo "    See infrastructure/iam-policy.json for required permissions"
    exit 1
fi

# Clean up
rm lambda_function.zip

echo "✅ Deployment complete!"
echo "💡 Function name: $FUNCTION_NAME"
echo "🌍 Region: $AWS_REGION"
echo "👤 Profile: $AWS_PROFILE" 