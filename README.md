# Automated Daily Briefing & Weather AI Agent

An AI app that runs **by itself every morning**: it collects weather, AWS announcements, tech news and your tasks, asks **Amazon Bedrock** to write a short briefing, and emails it through **Amazon SNS**.

```
EventBridge Scheduler (09:00 Asia/Kolkata)
        │  invokes
        ▼
     Lambda ──► Open-Meteo (weather) ─┐
        │  ├──► AWS What's New RSS ───┼─► JSON data ─► Amazon Bedrock (Converse API)
        │  ├──► Tech news RSS ────────┤                       │ briefing text
        │  └──► DAILY_TASKS env var ──┘                       ▼
        └──────────────────────────────────────────────► Amazon SNS ─► your email
                    all steps log JSON to CloudWatch Logs
```

## Quick start (TL;DR)
```bash
aws configure                              # once: access key, secret, region us-east-1
python3 local_run.py --no-ai               # local test, no AWS needed
python3 local_run.py                       # local test with Bedrock
# edit EMAIL in scripts/config.sh, then:
./scripts/deploy.sh                        # creates everything on AWS
# click "Confirm subscription" in the email AWS sends you
aws lambda invoke --function-name daily-briefing-agent --region us-east-1 out.json && cat out.json
```

## Dashboard
A Next.js dashboard in `frontend/` edits these settings live and shows real run history and health. See `frontend/README.md`.

## Who sends and who receives the email?
- **Sender:** Amazon SNS (from an AWS address such as `no-reply@sns.amazonaws.com`). No Gmail login or password is ever given to AWS.
- **Recipient:** the address in `EMAIL` (`scripts/config.sh`). It receives the briefing every day at the scheduled time **only after** it clicks *Confirm subscription* in the AWS confirmation email (check spam).
- **Add more recipients:** `aws sns subscribe --topic-arn <TOPIC_ARN> --protocol email --notification-endpoint other@example.com`
- **Stop emails:** click *Unsubscribe* at the bottom of any briefing, or run `cleanup.sh`.

## AWS credentials and security
- `deploy.sh` and `cleanup.sh` use whatever credentials the AWS CLI has (`aws configure`, or `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` environment variables). The IAM user needs permission to manage IAM roles, Lambda, SNS, EventBridge Scheduler and CloudWatch Logs.
- **Never** paste access keys into chats, code, screenshots or Git. If a key is exposed, deactivate it in *IAM → Users → Security credentials* and create a new one.
- The Lambda itself has no keys: it uses its IAM role.

## Project layout
| File | Purpose |
|---|---|
| `src/handler.py` | Lambda entry point (`src.handler.lambda_handler`) |
| `src/config.py` | All settings from environment variables |
| `src/weather_client.py` | Open-Meteo weather (no API key), stale check |
| `src/news_client.py` | AWS RSS feed, Hacker News API (RSS backup) |
| `src/billing_client.py` | Month-to-date spend, credits applied, forecast (Cost Explorer) |
| `src/tasks_client.py` | Tasks extracted from Gmail (label `tasks`) via IMAP + Bedrock |
| `src/calendar_client.py` | Today's events from a Google Calendar iCal link (no OAuth) |
| `src/bedrock_client.py` | Bedrock Runtime **Converse** API |
| `src/briefing.py` | Collect → prompt → Bedrock → safe fallback |
| `src/notifier.py` | SNS publish |
| `src/remote_settings.py` | Settings saved from the dashboard (SSM) override env defaults |
| `src/run_store.py` | Saves each run to DynamoDB (history for the dashboard) |
| `src/utils.py` | JSON logging, timers, HTTP helper, `SourceResult` |
| `local_run.py` | CLI to generate a briefing now |
| `iam/`, `scripts/` | IAM policies, deploy and cleanup scripts |

**Honesty rules:** every source returns `ok`, `stale` or `unavailable`. A failed source never stops the run; the prompt forbids inventing data and requires a "DATA NOTES" section. If Bedrock itself fails, a plain (non-AI) briefing of the raw data is still emailed.

## Environment variables
| Variable | Default | Meaning |
|---|---|---|
| `CITY` | Indore | City for weather |
| `TIMEZONE` | Asia/Kolkata | Dates and forecast timezone |
| `TEMP_UNITS` | celsius | `celsius` or `fahrenheit` |
| `USER_NAME` | (empty) | Fallback name in greeting; set yours in the dashboard Settings |
| `BRIEFING_TOPICS` | weather,aws,tech,calendar,tasks | Sections to include |
| `GMAIL_USER` | – | Gmail address to read tasks from (empty = email tasks off) |
| `GMAIL_LABEL` | INBOX | Mailbox/label scanned for the last 24 h (INBOX = automatic; set e.g. `tasks` to limit) |
| `GMAIL_PASSWORD_PARAM` | /daily-briefing/gmail-app-password | SSM SecureString holding the app password |
| `DAILY_TASKS` | – | Optional fixed tasks separated by `;`, added to the email tasks |
| `CALENDAR_ICS_URL` | – | Secret iCal address of your Google Calendar (adds today's events). Treat as a password |
| `HN_API_URL` | Hacker News Firebase API | Tech news source; `TECH_FEED_URL` (RSS) is the automatic backup |
| `BEDROCK_REGION` | us-east-1 | Region for Bedrock (`AWS_REGION` is reserved in Lambda) |
| `MODEL_ID` | us.amazon.nova-lite-v1:0 | Model or inference profile ID |
| `MAX_TOKENS` / `TEMPERATURE` | 800 / 0.3 | Generation settings |
| `GEOCODING_URL`, `WEATHER_URL`, `AWS_FEED_URL`, `TECH_FEED_URL` | Open-Meteo, AWS, hnrss | API endpoints |
| `MAX_NEWS_ITEMS`, `HTTP_TIMEOUT`, `STALE_AFTER_MINUTES` | 5, 8, 180 | Tuning |
| `SNS_TOPIC_ARN` | – | Set automatically by deploy |
| `EMAIL_SUBJECT_PREFIX` | Daily Briefing | Subject prefix |
| `DRY_RUN` | false | `true` = never publish to SNS |

## Tasks and updates from Gmail (optional, automatic)
Every run, the agent reads your **last 24 hours of inbox mail** (read-only, IMAP) and Bedrock picks out what needs attention: action items, deadlines and important updates from GitHub and similar tools (review requests, assigned issues, failed builds). Promotions and newsletters are skipped. Email text is untrusted data; instructions inside emails are ignored.
Privacy: the email snippets (first 500 characters of up to 30 messages) are sent to Bedrock in your own AWS account. To limit what the agent sees, set `GMAIL_LABEL` to a label such as `tasks` and only label emails you want scanned.
1. Google Account > Security > turn on 2-Step Verification, then create an **App password**.
2. Store it yourself in AWS (never paste it in chat, code or Git):
   ```bash
   aws ssm put-parameter --region us-east-1 --name /daily-briefing/gmail-app-password --type SecureString --value 'YOUR_APP_PASSWORD'
   ```
3. Set `GMAIL_USER` in `scripts/config.sh`, then `./scripts/deploy.sh` (the Lambda role gets `ssm:GetParameter` on just that parameter).
4. Local testing: `export GMAIL_APP_PASSWORD=...` in your terminal only.
If Gmail is unreachable the email says so instead of guessing. Revoke the app password anytime in your Google account.

## AWS billing and credits (optional)
Topic `billing` adds these bullets to the email, in this fixed order:
```
- Month-to-date usage: 355.28 USD
- Credits applied this month: 355.28 USD
- Month-to-date net charge: 0.00 USD
- Yesterday's usage: 12.43 USD
- Forecast month-end usage: 380.72 USD
- Top services: (top 5, with amounts)
```
The email contains only these figures, with no caveats or notes.
- **One-time:** the account owner opens *Billing and Cost Management > Cost Explorer* and enables it (data appears within ~24 h). Without it the email says billing is unavailable.
- **Limits (documentation only, not shown in the email):** data lags up to 24 h, and the **remaining credit balance is not exposed by any AWS API** (see Billing > Credits in the console).
- **Cost:** each Cost Explorer request is about $0.01 (about 4 per run, roughly $1.20/month at one run a day). Remove `billing` from `BRIEFING_TOPICS` to turn it off.
- **IAM:** the Lambda role gets `ce:GetCostAndUsage` and `ce:GetCostForecast` only (read-only).

## Google Calendar setup (optional)
1. Google Calendar (web) > Settings > select your calendar > **Integrate calendar**.
2. Copy **Secret address in iCal format** (a long `.ics` link). Anyone with it can read the calendar, so never share or commit it. If leaked, click *Reset* on that page.
3. Put it in `CALENDAR_ICS_URL` in `scripts/config.sh` and run `./scripts/deploy.sh`. Locally: add it to `.env`.
The Lambda only reads this link; it never gets access to your Google account. The URL is not written to logs. It is stored as a Lambda environment variable, so limit who can view your Lambda configuration.

## 1. Prerequisites
- AWS account, [AWS CLI v2](https://aws.amazon.com/cli/) configured (`aws configure`), Python 3.9+ (Lambda uses 3.12), `zip`.
- **Bedrock model access:** in the console open *Amazon Bedrock → Model catalog*, pick your model and make sure it is enabled/available for your account (some providers, e.g. Anthropic, ask for a one-time use-case form; Amazon Nova models usually work immediately). Use a region where the model is offered.
- Model IDs: newer models require an **inference profile ID** with a prefix (`us.`, `eu.`, `apac.`, `global.`). Find it under *Bedrock → Cross-region inference*, or `aws bedrock list-inference-profiles --region us-east-1`. Example: `MODEL_ID=us.amazon.nova-lite-v1:0`.

## 2. Test locally first
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python local_run.py --no-ai      # no AWS needed: proves weather/news collection
python local_run.py              # full flow with Bedrock (uses your AWS credentials)
python local_run.py --city Delhi --model-id apac.amazon.nova-lite-v1:0 --region ap-south-1
python local_run.py --send       # also emails via SNS (set SNS_TOPIC_ARN after step 3)
python -m unittest discover tests
```
Copy `.env.example` to `.env` to keep local settings (auto-loaded).

## 3. Deploy (one command)
Edit `scripts/config.sh` (at least `EMAIL`, region, model), then:
```bash
./scripts/deploy.sh
```
It creates the SNS topic and subscription, both IAM roles, the Lambda function and the EventBridge schedule. Manual equivalents are below.

### 3a. SNS + email confirmation
```bash
aws sns create-topic --name daily-briefing
aws sns subscribe --topic-arn <TOPIC_ARN> --protocol email --notification-endpoint you@example.com
```
**Confirmation step:** AWS emails "AWS Notification - Subscription Confirmation". Click **Confirm subscription** (check spam). Until you do, no briefing is delivered. Verify: `aws sns list-subscriptions-by-topic --topic-arn <TOPIC_ARN>` should show a real ARN, not `PendingConfirmation`.

### 3b. IAM (least privilege)
- Lambda role trust: `iam/lambda-trust.json`; permissions: `AWSLambdaBasicExecutionRole` (CloudWatch logs) + `iam/lambda-policy.json` (only `bedrock:InvokeModel` and `sns:Publish` on your topic).
- Scheduler role trust: `iam/scheduler-trust.json`; permissions: `iam/scheduler-policy.json` (only `lambda:InvokeFunction` on this function).

### 3c. Lambda
Runtime Python 3.12, handler `src.handler.lambda_handler`, timeout 60 s, memory 256 MB, zip of the `src/` folder (no extra dependencies), environment variables from the table above.

### 3d. EventBridge Scheduler
Console: *EventBridge → Scheduler → Create schedule* → Recurring, cron `0 9 * * ? *`, **Time zone `Asia/Kolkata`**, flexible window Off, target Lambda function, execution role = scheduler role. CLI is in `deploy.sh`. To change time, edit `SCHEDULE` and re-run deploy.

### 3e. Automatic deploys with GitHub Actions
`.github/workflows/deploy.yml` runs the unit tests on every push and pull request, and deploys to AWS when agent code, scripts or IAM policies change on `main` (or when you click *Run workflow*; tick *smoke_test* to also invoke the Lambda, which sends a real email).
- **No AWS keys are stored in GitHub.** The workflow signs in with GitHub OIDC and assumes the role `daily-briefing-github-deploy`, which only this repo's `main` branch can use and which is limited to this project's resources (`iam/github-deploy-policy.json`).
- **One-time setup** (needs AWS admin rights and `gh` logged in):
  ```bash
  REPO=owner/name EMAIL=you@example.com CITY=Indore GMAIL_USER=you@gmail.com \
  CALENDAR_ICS_URL='https://calendar.google.com/...basic.ics' ./scripts/setup-github-actions.sh
  ```
  It creates the OIDC provider and role and sets the repository **variables** `AWS_REGION, AWS_ROLE_ARN, EMAIL, CITY, TIMEZONE, SCHEDULE, MODEL_ID, BEDROCK_REGION, USER_NAME, BRIEFING_TOPICS, GMAIL_USER, GMAIL_LABEL` and the **secret** `CALENDAR_ICS_URL`. Change a value later under *Settings > Secrets and variables > Actions*, then re-run the workflow.
- The Gmail app password is not stored in GitHub. It stays in AWS SSM (step "Tasks and updates from Gmail").

## 4. Demo: the autonomous flow
1. Trigger immediately: `aws lambda invoke --function-name daily-briefing-agent --region us-east-1 out.json && cat out.json`
2. **Live scheduled demo:** set `SCHEDULE="cron(<minute+3> <hour> * * ? *)"` to a few minutes ahead, re-run `deploy.sh`, and wait. Do not touch anything: the email arrives on its own. Then restore 9:00.
3. Show the email, then the CloudWatch logs (below).

## 5. Verify in CloudWatch
Console: *CloudWatch → Log groups → `/aws/lambda/daily-briefing-agent`*. Or:
```bash
aws logs tail /aws/lambda/daily-briefing-agent --since 1h --region us-east-1
```
Expected event sequence: `scheduler.invoked` → `config.loaded` → `data.weather.start/end` → `data.aws_announcements…` → `data.summary` → `bedrock.invoke.start/end` → `bedrock.usage` → `sns.publish.start/end` → `sns.published` → `run.success` (with `duration_ms`). Failures appear as `*.failed` / `*.error` at WARNING/ERROR.
Logs Insights example:
```
fields @timestamp, event, duration_ms | filter level = "ERROR" or event = "run.success" | sort @timestamp desc
```

## 6. Troubleshooting
| Symptom | Fix |
|---|---|
| No email | Confirm the SNS subscription (spam folder); check `sns.published` in logs |
| `AccessDeniedException` on Bedrock | Model not enabled for the account/region, or `MODEL_ID` ARN not covered by IAM policy; check `BEDROCK_REGION` |
| `ValidationException: on-demand throughput isn't supported` | Use an inference profile ID (`us.`/`apac.`/`global.` prefix) |
| Email says "AI summary unavailable" | Bedrock failed; see `bedrock.failed_using_fallback` in logs |
| Weather "Unavailable" | City typo or network/API outage; the rest still works |
| Schedule never fires | Schedule state must be ENABLED; check the scheduler role's permission on the Lambda ARN; check the timezone; `aws scheduler get-schedule --name daily-briefing-9am` |
| Lambda timeout | Raise timeout; lower `HTTP_TIMEOUT`/`MAX_NEWS_ITEMS` |
| `Runtime.ImportModuleError` | Zip must contain the `src/` folder at its root |
| Role cannot be assumed right after creation | Wait ~10 s and retry (IAM propagation) |

## 7. Cleanup
```bash
./scripts/cleanup.sh
```
Removes the schedule, Lambda, SNS topic (and subscription), both IAM roles and the log group. Bedrock has no standing cost; you only pay per invocation, so leaving the schedule on costs a fraction of a cent per day.
