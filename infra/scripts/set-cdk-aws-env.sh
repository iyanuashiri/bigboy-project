#!/usr/bin/env bash
# Source before cdk deploy (Git Bash / WSL / macOS):  source ./scripts/set-cdk-aws-env.sh
set -e
eval "$(aws configure export-credentials --format env)"
export CDK_DEFAULT_REGION="${CDK_DEFAULT_REGION:-us-east-1}"
export CDK_DEFAULT_ACCOUNT="${CDK_DEFAULT_ACCOUNT:-$(aws sts get-caller-identity --query Account --output text)}"
echo "CDK_DEFAULT_ACCOUNT=${CDK_DEFAULT_ACCOUNT} CDK_DEFAULT_REGION=${CDK_DEFAULT_REGION} (session exported)"
