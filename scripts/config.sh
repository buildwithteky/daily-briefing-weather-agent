# ---- Edit these, then run scripts/deploy.sh ----
# Every value can also be supplied by the environment (GitHub Actions uses repository variables).
export AWS_REGION="${AWS_REGION:-us-east-1}"                 # region for Lambda, SNS, Scheduler
export EMAIL="${EMAIL:-you@example.com}"                     # where the briefing is delivered (edit me)
export CITY="${CITY:-Indore}"
export TIMEZONE="${TIMEZONE:-Asia/Kolkata}"
export SCHEDULE="${SCHEDULE:-cron(0 9 * * ? *)}"             # every day 09:00 in $TIMEZONE
export MODEL_ID="${MODEL_ID:-us.amazon.nova-lite-v1:0}"      # or a Claude inference profile ID
export BEDROCK_REGION="${BEDROCK_REGION:-us-east-1}"
export USER_NAME="${USER_NAME:-}"                            # optional fallback; set your name in the dashboard Settings
# Optional fixed tasks (separated by ;). Leave empty: tasks come from Gmail below.
export DAILY_TASKS="${DAILY_TASKS:-}"
# Emails from the last 24h in this mailbox are scanned for tasks/updates (GitHub etc.).
# INBOX = automatic. Use a label name (e.g. tasks) to limit what the agent can see.
export GMAIL_USER="${GMAIL_USER:-}"                          # your Gmail address; empty = email tasks off
export GMAIL_LABEL="${GMAIL_LABEL:-INBOX}"
export BRIEFING_TOPICS="${BRIEFING_TOPICS:-weather,aws,tech,calendar,tasks,billing}"
# Google Calendar > Settings > your calendar > Integrate calendar > "Secret address in iCal format".
# Treat it like a password: do not commit or share it. Leave empty to skip the calendar.
export CALENDAR_ICS_URL="${CALENDAR_ICS_URL:-}"   # pass it in the environment (GitHub secret); never hard-code

export FN_NAME="daily-briefing-agent"
export TOPIC_NAME="daily-briefing"
export LAMBDA_ROLE="daily-briefing-lambda-role"
export SCHED_ROLE="daily-briefing-scheduler-role"
export SCHEDULE_NAME="daily-briefing-9am"
