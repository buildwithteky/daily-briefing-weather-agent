#!/usr/bin/env bash
# One-time setup so .github/workflows/deploy.yml can deploy without stored AWS keys:
#   1. AWS: GitHub OIDC provider + a deploy role that ONLY your repo's main branch can assume
#   2. GitHub: repository variables (settings) and the calendar link as a secret
# Needs: aws CLI (admin-level rights, once) and gh CLI logged in with repo access.
# Usage: REPO=owner/name EMAIL=you@example.com CITY=Bhopal GMAIL_USER=you@gmail.com \
#        CALENDAR_ICS_URL=... ./scripts/setup-github-actions.sh
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/config.sh
: "${REPO:?Set REPO=owner/name}"
ROLE=daily-briefing-github-deploy
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OIDC_ARN="arn:aws:iam::$ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"

echo ">> GitHub OIDC provider"
aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$OIDC_ARN" >/dev/null 2>&1 || \
  aws iam create-open-id-connect-provider --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 >/dev/null

echo ">> Deploy role (only $REPO on main)"
cat > /tmp/gh-trust.json <<JSON
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Federated":"$OIDC_ARN"},
 "Action":"sts:AssumeRoleWithWebIdentity",
 "Condition":{"StringEquals":{"token.actions.githubusercontent.com:aud":"sts.amazonaws.com",
 "token.actions.githubusercontent.com:sub":"repo:$REPO:ref:refs/heads/main"}}}]}
JSON
aws iam create-role --role-name "$ROLE" --assume-role-policy-document file:///tmp/gh-trust.json >/dev/null 2>&1 || \
  aws iam update-assume-role-policy --role-name "$ROLE" --policy-document file:///tmp/gh-trust.json
sed "s#__ACCOUNT_ID__#$ACCOUNT_ID#g" iam/github-deploy-policy.json > /tmp/gh-policy.json
aws iam put-role-policy --role-name "$ROLE" --policy-name deploy-daily-briefing --policy-document file:///tmp/gh-policy.json
ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE"

echo ">> GitHub repository variables"
for v in AWS_REGION EMAIL CITY TIMEZONE SCHEDULE MODEL_ID BEDROCK_REGION USER_NAME BRIEFING_TOPICS GMAIL_USER GMAIL_LABEL; do
  [[ -n "${!v}" ]] && gh variable set "$v" --repo "$REPO" --body "${!v}"
done
gh variable set AWS_ROLE_ARN --repo "$REPO" --body "$ROLE_ARN"
if [[ -n "${CALENDAR_ICS_URL:-}" ]]; then
  gh secret set CALENDAR_ICS_URL --repo "$REPO" --body "$CALENDAR_ICS_URL"
fi
rm -f /tmp/gh-trust.json /tmp/gh-policy.json
echo "DONE. Role: $ROLE_ARN"
