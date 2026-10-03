from tutorial_lib import *

S = []
def slide(f): S.append(f); return f

K4 = "Part 4 | Deploy to AWS"


@slide
def s_deploy_overview(d):
    d.slide("Deployment overview", K4)
    items = [("SNS topic + email subscription", "where the briefing goes"), ("DynamoDB table", "run history, TTL 30 days"),
             ("Lambda IAM role", "Bedrock + SNS + SSM + DynamoDB"), ("Lambda function", "python3.12, 60 s, 256 MB"),
             ("Scheduler IAM role", "may invoke only this Lambda"), ("EventBridge schedule", "cron(0 9 * * ? *) Asia/Kolkata")]
    for i, (t, s) in enumerate(items):
        x, y = 56 + (i % 2) * 400, 125 + (i // 2) * 105
        d.node(x, y, 380, 85, t, s, white, DARK, ORANGE, 15)
        d.badge(x - 4, y + 4, i + 1, 13)
    d.callout(880, 125, 344, "One command", "<font name='Courier'>./scripts/deploy.sh</font> creates all six. It is safe to re-run.", GREEN)
    d.callout(880, 250, 344, "Order matters", "Roles must exist before the Lambda; the Lambda must exist before the schedule can target it.", AMBER)
    d.para(56, 470, 1168, "The next slides do each step by hand so you understand it. <b>After learning, use the script.</b>", size=16)
    d.code(56, 510, 1168, ["$ aws lambda get-function --function-name daily-briefing-agent    # after deploy: proves step 4",
                            "$ aws scheduler get-schedule --name daily-briefing-9am           # after deploy: proves step 6"], size=12, title="how you will verify")


@slide
def s_sns(d):
    d.slide("Step 1: SNS topic and email subscription", K4)
    d.code(56, 125, 700, [
        "$ aws sns create-topic --name daily-briefing --region us-east-1",
        "= {\"TopicArn\": \"arn:aws:sns:us-east-1:123456789012:daily-briefing\"}",
        "",
        "$ aws sns subscribe --region us-east-1 \\",
        "    --topic-arn arn:aws:sns:us-east-1:123456789012:daily-briefing \\",
        "    --protocol email --notification-endpoint you@example.com",
        "= {\"SubscriptionArn\": \"pending confirmation\"}",
        "",
        "# open the email from AWS and click  Confirm subscription",
        "$ aws sns list-subscriptions-by-topic --topic-arn <arn>",
        "= \"SubscriptionArn\": \"arn:aws:sns:us-east-1:...:daily-briefing:7b44...\""], size=11.8, title="terminal")
    d.callout(56, 425, 700, "Why the confirmation step", "AWS only sends email to people who confirm. <b>Until you click the link, no briefing arrives.</b>", AMBER)
    d.callout(790, 425, 434, "Expected result", "The subscription shows a real ARN, not <b>PendingConfirmation</b>.", GREEN)
    d.para(56, 555, 1168, "SNS sends from an AWS address (no-reply@sns.amazonaws.com); your inbox address is the <b>recipient</b>, no password is ever given to AWS.", size=14, color=GREY)


@slide
def s_iam(d):
    d.slide("Step 2: IAM roles and least privilege", K4)
    d.code(56, 125, 600, [
        "// Lambda role permissions (iam/lambda-policy.json)",
        "{ \"Sid\": \"InvokeBedrockModels\", \"Action\": \"bedrock:InvokeModel\",",
        "  \"Resource\": [\"arn:aws:bedrock:*::foundation-model/*\",",
        "    \"arn:aws:bedrock:*:<acct>:inference-profile/*\"] },",
        "{ \"Sid\": \"PublishBriefing\", \"Action\": \"sns:Publish\",",
        "  \"Resource\": \"<topic-arn>\" },",
        "{ \"Sid\": \"ReadAppParameters\", \"Action\": \"ssm:GetParameter\",",
        "  \"Resource\": [\".../gmail-app-password\", \".../settings\"] },",
        "{ \"Sid\": \"SaveRunHistory\", \"Action\": \"dynamodb:PutItem\",",
        "  \"Resource\": \".../table/daily-briefing-runs\" },",
        "{ \"Sid\": \"ReadBillingData\", \"Action\": [\"ce:GetCostAndUsage\",",
        "  \"ce:GetCostForecast\"], \"Resource\": \"*\" }",
        "// + AWSLambdaBasicExecutionRole (CloudWatch Logs)"], size=11, title="lambda role")
    d.code(680, 125, 544, [
        "// Scheduler role: may invoke ONLY this Lambda",
        "{ \"Action\": \"lambda:InvokeFunction\",",
        "  \"Resource\": [\"<lambda-arn>\", \"<lambda-arn>:*\"] }",
        "",
        "// Trust policies: who may assume each role",
        "Lambda role     -> lambda.amazonaws.com",
        "Scheduler role  -> scheduler.amazonaws.com"], size=11.5, title="scheduler role + trust")
    d.callout(680, 340, 544, "Why least privilege", "If the code or a key is ever compromised, damage is limited to publishing one topic and calling one model.", RED)
    d.callout(680, 470, 544, "Expected result", "Two roles exist: <font name='Courier'>aws iam get-role --role-name daily-briefing-lambda-role</font> returns the role.", GREEN)
    d.para(56, 560, 600, "Note: Cost Explorer actions do not support resource restrictions, so <b>Resource: \"*\"</b> is required for them.", size=13, color=GREY)


@slide
def s_data(d):
    d.slide("Step 3: DynamoDB table and secrets", K4)
    d.code(56, 125, 720, [
        "$ aws dynamodb create-table --table-name daily-briefing-runs \\",
        "    --billing-mode PAY_PER_REQUEST \\",
        "    --attribute-definitions AttributeName=pk,AttributeType=S \\",
        "                            AttributeName=startedAt,AttributeType=S \\",
        "    --key-schema AttributeName=pk,KeyType=HASH \\",
        "                 AttributeName=startedAt,KeyType=RANGE",
        "$ aws dynamodb update-time-to-live --table-name daily-briefing-runs \\",
        "    --time-to-live-specification Enabled=true,AttributeName=ttl",
        "",
        "$ aws ssm put-parameter --name /daily-briefing/gmail-app-password \\",
        "    --type SecureString --value '<app-password>'"], size=11.6, title="terminal")
    d.callout(56, 385, 720, "Why DynamoDB + TTL", "One item per run, newest first for the dashboard. <b>TTL</b> auto-deletes items after 30 days, so it never grows or costs.")
    d.callout(56, 500, 720, "Why SSM SecureString", "Encrypted at rest, fetched by the Lambda at runtime, never stored in code or environment variables.", ORANGE)
    d.callout(810, 125, 414, "Expected result", "<b>TableStatus: ACTIVE</b> and TTL ENABLED. <font name='Courier'>aws ssm get-parameter --name ... --query Parameter.Name</font> shows the name (not the value).", GREEN)
    d.callout(810, 315, 414, "Secret handling", "Type the app password only in your own terminal. Never paste it into chat, tickets or commits.", RED)


@slide
def s_lambda(d):
    d.slide("Step 4: package and create the Lambda", K4)
    d.code(56, 125, 700, [
        "$ zip -r briefing.zip src -x '*__pycache__*'",
        "$ aws lambda create-function \\",
        "    --function-name daily-briefing-agent \\",
        "    --runtime python3.12 --handler src.handler.lambda_handler \\",
        "    --role arn:aws:iam::<acct>:role/daily-briefing-lambda-role \\",
        "    --timeout 60 --memory-size 256 \\",
        "    --zip-file fileb://briefing.zip \\",
        "    --environment file://env.json",
        "",
        "# env.json",
        "{\"Variables\": {\"CITY\":\"Indore\",\"TIMEZONE\":\"Asia/Kolkata\",",
        "  \"MODEL_ID\":\"us.amazon.nova-lite-v1:0\",",
        "  \"BEDROCK_REGION\":\"us-east-1\",\"SNS_TOPIC_ARN\":\"<arn>\"}}"], size=11.6, title="terminal")
    rows = [["Setting", "Value", "Why"],
            ["Runtime", "python3.12", "Includes boto3; no dependency layer"],
            ["Handler", "src.handler.lambda_handler", "folder.file.function"],
            ["Timeout", "60 s", "Runs take 12-30 s (email + AI)"],
            ["Memory", "256 MB", "Plenty; more memory = faster CPU"]]
    d.table(790, 125, [90, 190, 154], rows, size=12)
    d.callout(56, 470, 700, "Expected result", "<font name='Courier'>aws lambda invoke --function-name daily-briefing-agent out.json</font> then <font name='Courier'>cat out.json</font> shows <b>\"status\": \"delivered\"</b> and every source <b>ok</b>. An email arrives.", GREEN)
    d.callout(790, 350, 434, "No VPC on purpose", "The Lambda must reach public APIs. Putting it in a VPC would need a NAT gateway (~$30+/month) for no benefit here.", AMBER)


@slide
def s_scheduler(d):
    d.slide("Step 5: EventBridge Scheduler (the autonomous part)", K4)
    d.code(56, 125, 760, [
        "$ aws scheduler create-schedule --name daily-briefing-9am \\",
        "    --schedule-expression 'cron(0 9 * * ? *)' \\",
        "    --schedule-expression-timezone Asia/Kolkata \\",
        "    --flexible-time-window Mode=OFF \\",
        "    --target '{\"Arn\":\"<lambda-arn>\",",
        "               \"RoleArn\":\"<scheduler-role-arn>\",",
        "               \"Input\":\"{\\\"source\\\":\\\"eventbridge-scheduler\\\"}\"}'"], size=12, title="terminal")
    d.callout(56, 350, 760, "Reading the cron", "<font name='Courier'>cron(minutes hours day-of-month month day-of-week year)</font>. <b>0 9 * * ? *</b> = every day at 09:00 in the schedule's timezone (the timezone is the reason to prefer Scheduler over classic rules).")
    d.callout(56, 480, 760, "Why a target role", "The Scheduler service needs permission to call your Lambda. That is the Scheduler role from step 2.", ORANGE)
    d.callout(850, 125, 374, "Expected result", "<font name='Courier'>aws scheduler get-schedule --name daily-briefing-9am</font> shows <b>State: ENABLED</b> and the timezone.", GREEN)
    d.callout(850, 285, 374, "Live demo trick", "Temporarily set the time 3 minutes ahead, wait, and watch the email arrive with nobody touching anything.", AMBER)


@slide
def s_deploy_script(d):
    d.slide("The one-command deployment", K4)
    d.code(56, 125, 560, [
        "# scripts/config.sh  (edit the values)",
        "export EMAIL=\"you@example.com\"",
        "export CITY=\"Indore\"",
        "export TIMEZONE=\"Asia/Kolkata\"",
        "export SCHEDULE=\"cron(0 9 * * ? *)\"",
        "export MODEL_ID=\"us.amazon.nova-lite-v1:0\"",
        "export GMAIL_USER=\"\"        # empty = email tasks off",
        "# CALENDAR_ICS_URL: pass via environment",
        "",
        "$ ./scripts/deploy.sh"], size=12, title="config + run")
    d.code(640, 125, 584, [
        "= >> Account 123456789012, region us-east-1",
        "= >> SNS topic + email subscription",
        "=    CHECK YOUR INBOX and click 'Confirm subscription'",
        "= >> DynamoDB run-history table",
        "= >> Lambda execution role",
        "= >> Package + create/update Lambda",
        "= >> Scheduler role",
        "= >> EventBridge schedule: cron(0 9 * * ? *) (Asia/Kolkata)",
        "= DONE. Confirm the SNS email, then test the Lambda."], size=11.4, title="expected output")
    d.callout(56, 400, 560, "Why a script", "Repeatable and reviewable. Re-running updates the code and settings instead of duplicating resources (create-or-update logic).")
    d.callout(640, 355, 584, "Environment overrides", "Every value in config.sh accepts an environment variable of the same name. That is how <b>GitHub Actions</b> supplies values without editing files.", ORANGE)
    d.callout(56, 520, 1168, "Expected result", "Script exits 0. You have a working scheduled agent. Confirm the SNS email, invoke once to test, then let the 9:00 AM schedule prove it runs on its own.", GREEN)


@slide
def s_verify(d):
    d.slide("Step 6: verify the deployment", K4)
    d.code(56, 125, 740, [
        "$ aws lambda invoke --function-name daily-briefing-agent \\",
        "    --payload '{\"source\":\"manual\"}' \\",
        "    --cli-binary-format raw-in-base64-out out.json",
        "$ cat out.json",
        "= {\"statusCode\":200,\"message_id\":\"...\",\"ai_used\":true,",
        "=  \"sources\":{\"weather\":\"ok\",\"aws_announcements\":\"ok\",",
        "=  \"tech_news\":\"ok\",\"calendar\":\"ok\",\"daily_tasks\":\"ok\",",
        "=  \"aws_billing\":\"ok\"},\"subject\":\"...\",\"body\":\"...full email...\",",
        "=  \"duration_ms\":15573,\"status\":\"delivered\",\"sent\":true}   # shortened",
        "",
        "$ aws logs tail /aws/lambda/daily-briefing-agent --since 5m",
        "= ... scheduler.invoked ... data.weather.end ... bedrock.invoke.end",
        "= ... sns.published ... run.saved ... run.success"], size=11.6, title="terminal")
    d.callout(830, 125, 394, "Checklist", "<b>1</b> Email received<br/><b>2</b> All sources ok<br/><b>3</b> run.success in logs<br/><b>4</b> Schedule ENABLED<br/><b>5</b> Next morning: email arrives by itself", GREEN)
    d.callout(56, 430, 740, "If something is not ok", "A source shows <b>unavailable</b>: read its <b>data.*.failed</b> log line. No email: check the SNS subscription is confirmed and see the troubleshooting slides.", AMBER)


@slide
def s_ci(d):
    d.slide("Automate deploys with GitHub Actions (OIDC)", K4)
    d.code(56, 125, 640, [
        "# .github/workflows/deploy.yml (essentials)",
        "on:  push: { branches: [main], paths: [src/**, scripts/**, iam/**] }",
        "permissions: { id-token: write, contents: read }",
        "jobs:",
        "  test:   python -m unittest discover tests",
        "  deploy:",
        "    needs: test",
        "    steps:",
        "      - uses: aws-actions/configure-aws-credentials@v4",
        "        with: { role-to-assume: ${{ vars.AWS_ROLE_ARN }} }",
        "      - run: ./scripts/deploy.sh"], size=11.6, title="workflow")
    d.code(56, 385, 640, [
        "$ REPO=owner/name EMAIL=you@example.com CITY=Indore \\",
        "  ./scripts/setup-github-actions.sh"], size=11.6, title="one-time setup")
    d.callout(730, 125, 494, "Why OIDC, not access keys", "GitHub proves its identity to AWS with a short-lived token. <b>No long-term AWS keys are stored in GitHub</b>, so there is nothing to leak or rotate.", GREEN)
    d.callout(730, 305, 494, "What the setup script creates", "OIDC provider, a deploy role only <b>your repo's main branch</b> can assume, plus GitHub <b>variables</b> (region, email, city...) and a <b>secret</b> (calendar link).", ORANGE)
    d.callout(56, 500, 640, "Expected result", "Push to main: tests pass, then the deploy job updates Lambda. Green checkmarks in the Actions tab.", GREEN)
    d.callout(730, 470, 494, "Gotcha", "\"Not authorized to perform sts:AssumeRoleWithWebIdentity\" = the trust rule does not match the token subject. The setup script reads the right subject from GitHub.", RED)


# ------------------------------------------------------------------ PART 5
K5 = "Part 5 | Connect the frontend"


@slide
def s_fe_arch(d):
    d.slide("Frontend architecture and request flow", K5)
    d.node(56, 300, 200, 90, "Browser", "React dashboard", white, DARK)
    d.node(330, 270, 250, 150, "Next.js server", "/api routes (Node)", DARK, DARK, ORANGE, 18)
    d.arrow(256, 345, 330, 345, "fetch", DARK)
    for i, (t, s) in enumerate([("SSM + Scheduler", "settings, time, on/off"), ("Lambda", "Generate now"), ("DynamoDB", "run history"), ("SNS + health", "subscription, checks")]):
        d.node(700, 115 + i * 92, 250, 74, t, s, white, DARK, ORANGE, 15)
        d.arrow(580, 345, 700, 152 + i * 92, "", GREY)
    d.node(1000, 270, 224, 90, "Open-Meteo", "city search, weather", SOFT, DARK, GREEN, 14)
    d.arrow(256, 320, 1000, 300, "", GREEN, dash=True)
    d.callout(56, 520, 560, "Security by design", "<b>AWS credentials live only on the server</b> (.env.local). The browser never sees a key. Mutating routes reject cross-site requests.", GREEN)
    d.callout(650, 520, 574, "No login (yet)", "Run it only on your own computer. Before putting it on the internet, add authentication.", RED)


@slide
def s_fe_run(d):
    d.slide("Step 7: connect and run the dashboard", K5)
    d.code(56, 125, 600, [
        "$ cd frontend",
        "$ npm install",
        "$ cp .env.example .env.local     # then edit",
        "$ npm run dev",
        "= Local:  http://localhost:3000",
        "= Environments: .env.local",
        "= Ready in 1.6s"], size=12.5, title="terminal")
    d.code(56, 330, 600, [
        "# frontend/.env.local   (git-ignored, server-side only)",
        "AWS_ACCESS_KEY_ID=<your key>",
        "AWS_SECRET_ACCESS_KEY=<your secret>",
        "AWS_REGION=us-east-1",
        "BRIEFING_FUNCTION_NAME=daily-briefing-agent",
        "BRIEFING_SCHEDULE_NAME=daily-briefing-9am",
        "BRIEFING_RUNS_TABLE=daily-briefing-runs"], size=12, title=".env.local")
    rows = [["Route", "Backed by"],
            ["GET/PUT /api/settings", "SSM + Scheduler + SNS"],
            ["POST /api/generate", "Lambda invoke (sends real email)"],
            ["GET /api/runs", "DynamoDB history"],
            ["GET /api/health", "Live checks of 5 services"]]
    d.table(690, 125, [230, 304], rows, size=13.5)
    d.callout(690, 330, 534, "Why server routes", "The AWS SDK needs secrets, and secrets cannot live in browser code. The server routes are a thin, safe bridge.")
    d.callout(690, 460, 534, "Expected result", "<font name='Courier'>curl localhost:3000/api/settings</font> returns your city, time and email as JSON.", GREEN)
    d.para(56, 560, 600, "IAM for the dashboard user: ssm Get/PutParameter, scheduler Get/UpdateSchedule (+PassRole), lambda Invoke, sns Subscribe/List, dynamodb Query.", size=12.5, color=GREY)


@slide
def s_fe_test(d):
    d.slide("Test the dashboard end to end", K5)
    rows = [["Action", "Expected result"],
            ["Search a city (2+ letters), pick one, Save", "Weather card updates; next email uses that city"],
            ["Change delivery time, Save", "Countdown changes (EventBridge updated)"],
            ["Toggle daily automation off", "Health shows Schedule paused"],
            ["Generate briefing now", "Real email; new history row; diagram from real run"],
            ["Turn off \"Email me the briefing\"", "Run is Generated, not emailed"],
            ["View a history row", "Shows the exact briefing text"]]
    d.table(56, 125, [400, 768], rows, size=14)
    d.callout(56, 470, 1168, "Everything is real", "No mock data: history, health and settings come from your AWS account.", GREEN)


# ------------------------------------------------------------------ PART 6
K6 = "Part 6 | Production"


@slide
def s_monitor(d):
    d.slide("Logging and monitoring", K6)
    d.code(56, 125, 700, [
        "# CloudWatch Logs Insights: errors and slow runs",
        "fields @timestamp, event, level, duration_ms",
        "| filter level = \"ERROR\" or event = \"run.success\"",
        "| sort @timestamp desc | limit 20",
        "",
        "# Alarm: notify when the Lambda errors (recommended)",
        "$ aws cloudwatch put-metric-alarm --alarm-name briefing-errors \\",
        "    --namespace AWS/Lambda --metric-name Errors --statistic Sum \\",
        "    --dimensions Name=FunctionName,Value=daily-briefing-agent \\",
        "    --period 300 --evaluation-periods 1 --threshold 1 \\",
        "    --comparison-operator GreaterThanOrEqualToThreshold \\",
        "    --alarm-actions arn:aws:sns:us-east-1:<acct>:daily-briefing",
        "$ aws logs put-retention-policy --retention-in-days 30 \\",
        "    --log-group-name /aws/lambda/daily-briefing-agent"], size=11, title="queries and alarms")
    d.callout(790, 125, 434, "Three layers", "<b>Logs</b>: what happened. <b>Metrics</b>: Invocations, Errors, Duration. <b>Dashboard</b>: run history and health at a glance.")
    d.callout(790, 275, 434, "Built-in failure alert", "With \"Email me if a run fails\" on, a failed run emails you the error.", GREEN)
    d.callout(790, 395, 434, "Recommended hardening", "The alarm and 30-day log retention above are <b>not created by deploy.sh</b>. Add them for production.", AMBER)


@slide
def s_security(d):
    d.slide("Security considerations", K6)
    rows = [["Risk", "How this project handles it", "You should also"],
            ["Leaked AWS keys", "Lambda uses a role; CI uses OIDC; .env.local is git-ignored", "Rotate any key ever shown in chat or a screenshot"],
            ["Over-broad permissions", "Separate least-privilege roles per component", "Review policies when adding features"],
            ["Secrets in code", "SSM SecureString + GitHub secrets; iCal link never logged", "Reset the iCal link and app password if exposed"],
            ["Prompt injection via email", "Emails treated as data; size caps; output must be a JSON list", "Limit GMAIL_LABEL to only the mail you want scanned"],
            ["Unauthenticated dashboard", "Cross-site requests blocked; local use only", "Add authentication before any public hosting"],
            ["Privacy", "Email snippets go only to Bedrock in your own account", "Do not share briefings or logs publicly"]]
    y = d.table(56, 125, [250, 490, 428], rows, size=15.5)
    d.callout(56, y + 40, 1168, "Rule of thumb", "If a value would hurt in someone else's hands (key, password, secret link), it never belongs in code, chat, screenshots or Git.", RED)


@slide
def s_trouble1(d):
    d.slide("Troubleshooting (1 of 2)", K6)
    rows = [["Symptom", "Likely cause", "Fix"],
            ["<font name='Courier'>AccessDeniedException</font> from Bedrock", "Model not enabled, or IAM does not cover the model/profile", "Enable the model in the console; check MODEL_ID and BEDROCK_REGION and the role's bedrock:InvokeModel resources"],
            ["<font name='Courier'>on-demand throughput isn't supported</font>", "Used a raw model ID", "Use an inference profile ID (us. / apac. / global. prefix)"],
            ["No email arrives", "SNS subscription not confirmed", "Click the confirmation link; check spam; list subscriptions"],
            ["Email says \"AI summary unavailable\"", "Bedrock call failed; fallback used", "Search logs for bedrock.failed_using_fallback"],
            ["Weather \"Unavailable\"", "City typo or API outage", "Fix CITY; other sections still work"],
            ["Schedule never fires", "Disabled, wrong timezone, or role cannot invoke Lambda", "get-schedule: State, timezone; scheduler role policy"],
            ["<font name='Courier'>Runtime.ImportModuleError</font>", "Zip layout wrong", "Zip must contain the src/ folder at its root"]]
    d.table(56, 125, [330, 340, 498], rows, size=15)


@slide
def s_trouble2(d):
    d.slide("Troubleshooting (2 of 2)", K6)
    rows = [["Symptom", "Likely cause", "Fix"],
            ["Tasks: <font name='Courier'>mailbox/label not found</font>", "GMAIL_LABEL does not exist", "Use INBOX or create the label in Gmail"],
            ["Tasks: <font name='Courier'>AUTHENTICATIONFAILED</font>", "Wrong or revoked app password", "Create a new app password; overwrite the SSM parameter"],
            ["Calendar: \"did not return an iCal calendar\"", "Wrong URL", "Copy the Secret address in iCal format (ends .ics)"],
            ["Billing unavailable / AccessDenied", "Cost Explorer not enabled or role lacks ce:*", "Enable Cost Explorer; wait up to 24 h; check policy"],
            ["Lambda timeout", "Slow source (Gmail, billing) plus AI", "Raise timeout above 60 s or reduce topics"],
            ["Actions: <font name='Courier'>Not authorized ... AssumeRoleWithWebIdentity</font>", "OIDC trust subject mismatch", "Re-run setup-github-actions.sh"],
            ["Dashboard: \"AWS request failed\"", "Missing credentials or permission", "Check .env.local; restart npm run dev; check IAM"]]
    y = d.table(56, 125, [360, 340, 468], rows, size=14.5)
    d.callout(56, y + 40, 1168, "Debug method", "1) Which layer? (source, Bedrock, SNS, schedule). 2) Read the matching <b>.failed</b> or <b>.error</b> log line. 3) Reproduce locally with <font name='Courier'>local_run.py</font>.", ORANGE)


@slide
def s_cost(d):
    d.slide("Cost management", K6)
    rows = [["Service", "Typical usage (1 run / day)", "Approximate cost"],
            ["Lambda", "~30 runs/month, ~15 s each", "Free tier"],
            ["EventBridge Scheduler", "30 invocations/month", "Free tier"],
            ["Amazon Bedrock (Nova Lite)", "2 calls/run, a few thousand tokens", "Cents per month"],
            ["Amazon SNS email", "30 emails/month", "Free tier"],
            ["DynamoDB (on-demand) + SSM", "30 small items, 30-day TTL", "Well under $1"],
            ["Cost Explorer API", "~4 requests/run at $0.01", "About $1.20/month"],
            ["CloudWatch Logs", "Small JSON logs", "Cents; set retention"]]
    y = d.table(56, 125, [330, 470, 368], rows, size=16)
    d.callout(56, y + 40, 570, "Cost controls", "Remove <b>billing</b> from topics to drop the Cost Explorer charge. Use a small model. Keep log retention at 30 days. Add an AWS Budget alert.", GREEN)
    d.callout(654, y + 40, 570, "Note", "Figures are approximate and change over time. Check the AWS pricing pages before relying on them.", AMBER)


@slide
def s_checklist1(d):
    d.slide("Production-readiness checklist (1 of 2)", K6)
    cols = [("SECURITY", [
        "MFA on the AWS account; no root use",
        "Least-privilege roles (done in iam/)",
        "OIDC for CI; no stored AWS keys",
        "Secrets in SSM / GitHub secrets only",
        "Exposed keys and passwords rotated",
        "Dashboard behind authentication if hosted"]),
        ("RELIABILITY", [
        "Each source fails independently (done)",
        "Backup tech-news source (done)",
        "Fallback email when Bedrock fails (done)",
        "Lambda timeout > longest run (60 s)",
        "Schedule ENABLED, timezone verified",
        "Test invoke succeeds after every deploy"]),
        ("COST", [
        "AWS Budget alert created",
        "Small model chosen deliberately",
        "TTL on run history (done)",
        "Log retention set (30 days)",
        "Billing topic on only if wanted",
        "No unused resources left running"])]
    for i, (h, items) in enumerate(cols):
        x = 56 + i * 400
        d.node(x, 125, 370, 400, "", "", white, DARK)
        d.label(x + 20, 158, h, ORANGE, 14)
        y = 180
        for it in items:
            d.c.setStrokeColor(DARK); d.c.setLineWidth(1.5); d.c.rect(x + 20, d.Y(y + 20), 16, 16, fill=0, stroke=1)
            d.para(x + 46, y, 305, it, size=14)
            y += 55


@slide
def s_checklist2(d):
    d.slide("Production-readiness checklist (2 of 2)", K6)
    cols = [("MONITORING", [
        "Structured logs for every step (done)",
        "Logs Insights queries saved",
        "CloudWatch alarm on Lambda Errors",
        "Failure-alert email enabled",
        "Dashboard health checked weekly",
        "Run history reviewed (30 days)"]),
        ("ERROR HANDLING", [
        "Sources return unavailable, never crash",
        "AI told never to invent data",
        "Run failures re-raised and recorded",
        "Input caps on email text",
        "Settings validated (allow-list)",
        "Unit tests cover failure paths"]),
        ("DEPLOY VERIFICATION", [
        "Unit tests green in CI",
        "deploy.sh / Actions run succeeds",
        "SNS subscription confirmed",
        "Manual invoke: status delivered",
        "Next scheduled run arrives unaided",
        "Logs show run.success"])]
    for i, (h, items) in enumerate(cols):
        x = 56 + i * 400
        d.node(x, 125, 370, 400, "", "", white, DARK)
        d.label(x + 20, 158, h, ORANGE, 14)
        y = 180
        for it in items:
            d.c.setStrokeColor(DARK); d.c.setLineWidth(1.5); d.c.rect(x + 20, d.Y(y + 20), 16, 16, fill=0, stroke=1)
            d.para(x + 46, y, 305, it, size=14)
            y += 55
    d.para(56, 545, 1168, "Items marked <b>(done)</b> are built into this project. The rest are one-time tasks for you.", size=14, color=GREY)


@slide
def s_cleanup(d):
    d.slide("Clean up and next steps", K6)
    d.code(56, 125, 600, [
        "$ ./scripts/cleanup.sh",
        "= schedule, Lambda, SNS topic, IAM roles,",
        "= DynamoDB table, settings, log group deleted",
        "",
        "# the app password is kept on purpose; remove it too:",
        "$ aws ssm delete-parameter \\",
        "    --name /daily-briefing/gmail-app-password",
        "# GitHub deploy role (if you set up CI):",
        "$ aws iam delete-role-policy --role-name \\",
        "    daily-briefing-github-deploy --policy-name deploy-daily-briefing",
        "$ aws iam delete-role --role-name daily-briefing-github-deploy"], size=11.4, title="teardown")
    d.callout(56, 470, 600, "Why clean up", "Unused resources cost money and widen your attack surface. Delete what a workshop no longer needs.", AMBER)
    d.para(700, 125, 524, "<b>Where to go next</b>", size=20)
    d.bullets(700, 165, 524, [
        "Swap in your own data sources (a new file in <font name='Courier'>src/</font>, one line in <font name='Courier'>COLLECTORS</font>)",
        "Try another Bedrock model by changing MODEL_ID",
        "Add Cognito sign-in and host the dashboard",
        "Add a CloudWatch alarm and an AWS Budget",
        "Send a weekly summary with a second schedule"], size=16, gap=12)
    d.callout(700, 470, 524, "You built", "A scheduled, self-running AI application: <b>scheduled trigger > Lambda > data > Bedrock > briefing > SNS email</b>.", GREEN)
