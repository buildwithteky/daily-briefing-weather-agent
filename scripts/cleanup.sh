#!/usr/bin/env bash
# Deletes everything deploy.sh created.
cd "$(dirname "$0")/.."
source scripts/config.sh
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws scheduler delete-schedule --name "$SCHEDULE_NAME" --region "$AWS_REGION"
aws lambda delete-function --function-name "$FN_NAME" --region "$AWS_REGION"
aws sns delete-topic --topic-arn "arn:aws:sns:$AWS_REGION:$ACCOUNT_ID:$TOPIC_NAME" --region "$AWS_REGION"
aws iam delete-role-policy --role-name "$SCHED_ROLE" --policy-name invoke-briefing-lambda
aws iam delete-role --role-name "$SCHED_ROLE"
aws iam detach-role-policy --role-name "$LAMBDA_ROLE" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role-policy --role-name "$LAMBDA_ROLE" --policy-name briefing-bedrock-sns
aws iam delete-role --role-name "$LAMBDA_ROLE"
aws logs delete-log-group --log-group-name "/aws/lambda/$FN_NAME" --region "$AWS_REGION"
aws dynamodb delete-table --table-name daily-briefing-runs --region "$AWS_REGION" >/dev/null
aws ssm delete-parameter --name /daily-briefing/settings --region "$AWS_REGION" 2>/dev/null
echo "Cleanup complete. (The Gmail app password parameter is kept: delete it with aws ssm delete-parameter --name /daily-briefing/gmail-app-password)"
