#!/usr/bin/env bash
# Creates: SNS topic+email sub, IAM roles, Lambda, EventBridge schedule. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/config.sh
[[ "$EMAIL" == "you@example.com" ]] && { echo "Edit scripts/config.sh first (EMAIL)"; exit 1; }

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo ">> Account $ACCOUNT_ID, region $AWS_REGION"

echo ">> SNS topic + email subscription"
TOPIC_ARN=$(aws sns create-topic --name "$TOPIC_NAME" --region "$AWS_REGION" --query TopicArn --output text)
aws sns subscribe --topic-arn "$TOPIC_ARN" --protocol email --notification-endpoint "$EMAIL" --region "$AWS_REGION" >/dev/null
echo "   CHECK YOUR INBOX and click 'Confirm subscription' ($EMAIL)"

echo ">> DynamoDB run-history table"
aws dynamodb create-table --table-name daily-briefing-runs --billing-mode PAY_PER_REQUEST --region "$AWS_REGION" \
  --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=startedAt,AttributeType=S \
  --key-schema AttributeName=pk,KeyType=HASH AttributeName=startedAt,KeyType=RANGE >/dev/null 2>&1 || true
aws dynamodb wait table-exists --table-name daily-briefing-runs --region "$AWS_REGION"
aws dynamodb update-time-to-live --table-name daily-briefing-runs --region "$AWS_REGION" \
  --time-to-live-specification Enabled=true,AttributeName=ttl >/dev/null 2>&1 || true

echo ">> Lambda execution role"
aws iam create-role --role-name "$LAMBDA_ROLE" --assume-role-policy-document file://iam/lambda-trust.json >/dev/null 2>&1 || true
aws iam attach-role-policy --role-name "$LAMBDA_ROLE" \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
sed "s#__ACCOUNT_ID__#$ACCOUNT_ID#g; s#__TOPIC_ARN__#$TOPIC_ARN#g; s#__REGION__#$AWS_REGION#g" iam/lambda-policy.json > /tmp/lambda-policy.json
aws iam put-role-policy --role-name "$LAMBDA_ROLE" --policy-name briefing-bedrock-sns --policy-document file:///tmp/lambda-policy.json
LAMBDA_ROLE_ARN=$(aws iam get-role --role-name "$LAMBDA_ROLE" --query Role.Arn --output text)

echo ">> Package + create/update Lambda"
rm -f /tmp/briefing.zip && zip -qr /tmp/briefing.zip src -x '*__pycache__*'
export TOPIC_ARN
ENV=$(python3 -c 'import json,os;k="CITY TIMEZONE MODEL_ID BEDROCK_REGION USER_NAME BRIEFING_TOPICS DAILY_TASKS CALENDAR_ICS_URL GMAIL_USER GMAIL_LABEL".split();d={x:os.environ[x] for x in k};d["SNS_TOPIC_ARN"]=os.environ["TOPIC_ARN"];print(json.dumps({"Variables":d}))')
if aws lambda get-function --function-name "$FN_NAME" --region "$AWS_REGION" >/dev/null 2>&1; then
  aws lambda update-function-code --function-name "$FN_NAME" --zip-file fileb:///tmp/briefing.zip --region "$AWS_REGION" >/dev/null
  aws lambda wait function-updated --function-name "$FN_NAME" --region "$AWS_REGION"
  aws lambda update-function-configuration --function-name "$FN_NAME" --environment "$ENV" --region "$AWS_REGION" >/dev/null
else
  echo "   (waiting 10s for IAM role to propagate)"; sleep 10
  aws lambda create-function --function-name "$FN_NAME" --runtime python3.12 \
    --handler src.handler.lambda_handler --role "$LAMBDA_ROLE_ARN" --timeout 60 --memory-size 256 \
    --zip-file fileb:///tmp/briefing.zip --environment "$ENV" --region "$AWS_REGION" >/dev/null
fi
aws lambda wait function-active-v2 --function-name "$FN_NAME" --region "$AWS_REGION"
LAMBDA_ARN=$(aws lambda get-function --function-name "$FN_NAME" --region "$AWS_REGION" --query Configuration.FunctionArn --output text)

echo ">> Scheduler role"
aws iam create-role --role-name "$SCHED_ROLE" --assume-role-policy-document file://iam/scheduler-trust.json >/dev/null 2>&1 || true
sed "s#__LAMBDA_ARN__#$LAMBDA_ARN#g" iam/scheduler-policy.json > /tmp/scheduler-policy.json
aws iam put-role-policy --role-name "$SCHED_ROLE" --policy-name invoke-briefing-lambda --policy-document file:///tmp/scheduler-policy.json
SCHED_ROLE_ARN=$(aws iam get-role --role-name "$SCHED_ROLE" --query Role.Arn --output text)
sleep 8

echo ">> EventBridge schedule: $SCHEDULE ($TIMEZONE)"
TARGET="{\"Arn\":\"$LAMBDA_ARN\",\"RoleArn\":\"$SCHED_ROLE_ARN\",\"Input\":\"{\\\"source\\\":\\\"eventbridge-scheduler\\\"}\"}"
ARGS=(--name "$SCHEDULE_NAME" --schedule-expression "$SCHEDULE" --schedule-expression-timezone "$TIMEZONE"
      --flexible-time-window Mode=OFF --target "$TARGET" --region "$AWS_REGION")
aws scheduler create-schedule "${ARGS[@]}" >/dev/null 2>&1 || aws scheduler update-schedule "${ARGS[@]}" >/dev/null

echo "DONE. Confirm the SNS email, then test: aws lambda invoke --function-name $FN_NAME --region $AWS_REGION out.json && cat out.json"
