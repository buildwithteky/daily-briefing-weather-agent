from tutorial_lib import *

S = []
def slide(f): S.append(f); return f


@slide
def s_title(d):
    d.title_slide(["Build, Run & Deploy an", "Automated Daily Briefing", "AI Agent on AWS"],
                  ["EventBridge Scheduler > Lambda > Amazon Bedrock > SNS > your inbox.",
                   "A step-by-step tutorial: local development first, then production."],
                  ["PYTHON 3.12", "AWS LAMBDA", "AMAZON BEDROCK", "NEXT.JS"])
    for i, n in enumerate(["eventbridge", "lambda", "bedrock", "sns"]):
        d.icon(n, 860 + (i % 2) * 190, 170 + (i // 2) * 190, 150)


@slide
def s_overview(d):
    d.slide("What you will build", "Overview")
    d.bullets(56, 130, 560, [
        "<b>A serverless AI agent that runs by itself.</b> Every morning it wakes up without anyone clicking anything.",
        "It <b>collects live data</b>: weather, AWS announcements, tech news, your calendar, tasks from your email, and your AWS spend.",
        "<b>Amazon Bedrock</b> (a foundation model) reads the data and writes a short, friendly briefing.",
        "<b>Amazon SNS</b> emails it to you. A <b>dashboard</b> lets you change settings and see every run.",
        "If any source fails, the email says <b>\"unavailable\"</b>. The agent never makes data up."], size=17, gap=12)
    d.callout(56, 520, 560, "What you need to know", "Basic Python and a terminal. Every step explains <b>what</b> to do, <b>why</b>, and the <b>expected result</b>.")
    # sample email card
    c = d.c
    c.setFillColor(white); c.setStrokeColor(LINE); c.roundRect(680, d.Y(650), 544, 520, 4, fill=1, stroke=1)
    c.setFillColor(SOFT); c.rect(680, d.Y(190), 544, 60, fill=1, stroke=0)
    d.para(700, 138, 510, "<b>Daily Briefing - Indore - 29 Sep 2026</b>", size=15)
    d.para(700, 162, 510, "From: Amazon SNS   To: you", size=12, color=GREY)
    d.para(700, 206, 500,
           "<b>Good morning!</b><br/><br/>"
           "<b>Weather</b><br/>Clear sky, 31.2 C (feels like 31.4). Humidity 36%. Stay hydrated.<br/><br/>"
           "<b>AWS updates</b><br/>- Claude Sonnet 5.5 now available on AWS<br/>- Grok 4.7 now on Amazon Bedrock<br/><br/>"
           "<b>Tech news</b><br/>- Top Hacker News stories (5 headlines)<br/><br/>"
           "<b>Today's calendar</b><br/>- 20:00 - Demo Day<br/><br/>"
           "<b>Tasks and updates</b><br/>- Review failed tests on GitHub<br/><br/>"
           "<b>AWS billing</b><br/>- Month-to-date usage: 12.40 USD<br/>- Credits applied this month: 12.40 USD<br/>- Month-to-date net charge: 0.00 USD<br/>- Yesterday's usage, month-end forecast, top services", size=12, leading=15)
    d.chip(700, 614, "SAMPLE OUTPUT", fill=ORANGE, color=white, size=11)


@slide
def s_how(d):
    d.slide("How the agent works: six steps", "Overview")
    steps = [("Schedule fires", "EventBridge Scheduler calls the Lambda at 09:00 in your timezone."),
             ("Lambda starts", "Python code loads config and any settings saved from the dashboard."),
             ("Collect data", "Six sources are fetched. Each one can fail without stopping the rest."),
             ("AI summarises", "Amazon Bedrock turns the data into a short, structured briefing."),
             ("Email sent", "Amazon SNS delivers the briefing to your confirmed email address."),
             ("Run recorded", "Result saved to DynamoDB; every step logged to CloudWatch.")]
    for i, (t, s) in enumerate(steps):
        x, y = 56 + (i % 3) * 400, 130 + (i // 3) * 200
        d.node(x, y, 370, 170, "", "", white, DARK)
        d.badge(x + 32, y + 46, i + 1)
        d.para(x + 62, y + 32, 290, "<b>%s</b>" % t, size=19)
        d.para(x + 24, y + 82, 325, s, size=16, color=DARK)
    d.callout(56, 545, 1168, "Design principle", "<b>Never fabricate.</b> Every source returns a status: <b>ok</b>, <b>stale</b> or <b>unavailable</b>. The AI is told to say \"Unavailable right now\" instead of guessing. One failing API never blocks the email.", GREEN)


@slide
def s_arch(d):
    d.slide("Architecture", "Overview")
    d.group(40, 105, 870, 545, "AWS Cloud", "cloud")
    d.group(60, 142, 830, 494, "Region: us-east-1", "region")
    # core path
    d.tile(130, 320, "eventbridge", "EventBridge", "Scheduler (cron)")
    d.tile(340, 316, "lambda", "AWS Lambda", "Python 3.12 agent", 72)
    d.tile(340, 175, "bedrock", "Amazon Bedrock", "Converse API")
    d.tile(580, 320, "sns", "Amazon SNS", "email topic")
    d.arrow(168, 354, 296, 354, "invoke", DARK, loff=(0, -8))
    d.arrow(340, 282, 340, 312, "", DARK, both=True)
    d.arrow(384, 354, 538, 354, "publish", DARK, loff=(0, -8))
    # supporting services (dashed = reads/writes)
    d.tile(150, 490, "iam", "IAM roles", "least privilege")
    d.tile(310, 490, "ssm", "SSM Parameter Store", "settings + secrets")
    d.tile(480, 490, "dynamodb", "DynamoDB", "run history (30 d)")
    d.tile(650, 490, "cloudwatch", "CloudWatch Logs", "JSON logs")
    for tx in (150, 310, 480, 650):
        d.arrow(340, 440, tx, 484, "", GREY, dash=True)
    # outside the cloud: the user and the internet
    d.c.setFillColor(white); d.c.setStrokeColor(LINE); d.c.rect(940, d.Y(300), 300, 195, fill=1, stroke=1)
    d.icon("internet", 952, 114, 30)
    d.para(990, 121, 240, "<b>External data sources</b>", size=13)
    for i, t in enumerate(["Open-Meteo (weather)", "AWS What's New (RSS)", "Hacker News API", "Google Calendar (iCal)", "Gmail (IMAP, read-only)", "Cost Explorer (spend)"]):
        d.para(956, 160 + i * 22, 270, "- " + t, size=12.5, color=DARK)
    d.arrow(384, 336, 940, 215, "fetch", ORANGE, both=True, loff=(-30, -16))
    d.tile(1090, 320, "email", "Your inbox", "Gmail / any email", 56)
    d.arrow(612, 354, 1040, 354, "email", DARK, loff=(0, -8))
    d.para(56, 662, 1000, "Dashboard (Next.js, runs locally) talks to SSM, Scheduler, Lambda, DynamoDB and SNS through its own server routes. Icons: official AWS Architecture Icons.", size=12, color=GREY)


@slide
def s_flow(d):
    d.slide("Request and data flow", "Overview")
    rows = [["#", "From > To", "What travels", "Why"],
            ["1", "EventBridge > Lambda", "{\"source\": \"eventbridge-scheduler\"}", "Starts the run on time, no human needed"],
            ["2", "Lambda > SSM", "Saved settings (city, topics, name)", "Dashboard changes apply on the next run"],
            ["3", "Lambda > 6 sources (HTTPS)", "City, feed URLs, calendar link, IMAP login, cost query", "Fresh data every run"],
            ["4", "Lambda > Bedrock", "JSON of all source results + rules", "Model writes the briefing"],
            ["5", "Lambda > SNS > email", "Subject + body text", "Delivery to the user"],
            ["6", "Lambda > DynamoDB", "Status, duration, sources, body", "History shown on the dashboard"],
            ["7", "Dashboard > AWS", "Reads/writes via server routes", "Configure and monitor without the console"]]
    y = d.table(56, 130, [40, 270, 470, 388], rows, size=16)
    d.callout(56, y + 40, 1168, "Where secrets live", "Gmail app password: <b>SSM SecureString</b>. Calendar link: <b>Lambda env var / GitHub secret</b>. AWS keys: <b>never in code</b>. Lambda uses an <b>IAM role</b>, GitHub uses <b>OIDC</b>.", AMBER)


@slide
def s_services(d):
    d.slide("AWS services and why we use them", "Overview")
    cards = [("eventbridge", "EventBridge Scheduler", "Fires the agent daily (cron + timezone)", "Serverless cron, no server to keep on"),
             ("lambda", "AWS Lambda", "Runs the Python agent", "Pay per run; ~15 s a day; nothing to maintain"),
             ("bedrock", "Amazon Bedrock", "Writes the briefing, extracts tasks from email", "Managed models via one API; data stays in your account"),
             ("sns", "Amazon SNS", "Emails the briefing", "Simple email delivery with a confirmation step"),
             ("iam", "AWS IAM", "Least-privilege roles for Lambda, Scheduler, CI", "Only the permissions each part needs"),
             ("dynamodb", "Amazon DynamoDB", "Run history (auto-deleted after 30 days)", "On-demand, pennies, no tuning"),
             ("ssm", "SSM Parameter Store", "Dashboard settings and the Gmail app password", "Encrypted secrets and config, free tier"),
             ("cloudwatch", "Amazon CloudWatch", "Structured logs for every step", "Built in to Lambda; searchable with Logs Insights"),
             ("costexplorer", "AWS Cost Explorer", "Month-to-date spend and credits", "Official spend data via API")]
    for i, (ic, name, role, why) in enumerate(cards):
        x, y = 56 + (i % 3) * 400, 120 + (i // 3) * 176
        d.node(x, y, 368, 156, "", "", white, LINE, ORANGE)
        d.icon(ic, x + 16, y + 26, 64)
        d.para(x + 96, y + 24, 262, "<b>%s</b>" % name, size=16.5)
        d.para(x + 96, y + 52, 262, role, size=13, color=DARK)
        d.para(x + 96, y + 100, 262, why, size=12, color=GREY)
    d.para(56, 662, 1100, "The next nine slides explain each service in plain English: what it is, an everyday analogy, how this project uses it, the settings, and what to watch out for.", size=12.5, color=GREY)


@slide
def s_agenda(d):
    d.slide("Tutorial roadmap", "Overview")
    parts = [("PART 1", "Prerequisites and setup", "Accounts, tools, Bedrock access, repository, environment variables"),
             ("PART 2", "Build the agent", "Data sources, Bedrock client, briefing logic, Lambda handler"),
             ("PART 3", "Test locally", "Unit tests, local runs, failure experiments, reading logs"),
             ("PART 4", "Deploy to AWS", "SNS, IAM, DynamoDB, Lambda, Scheduler, verification, CI/CD"),
             ("PART 5", "Connect the frontend", "Server routes, .env.local, dashboard checks"),
             ("PART 6", "Go to production", "Monitoring, security, troubleshooting, cost, checklist")]
    for i, (p, t, s) in enumerate(parts):
        x, y = 56 + (i % 2) * 600, 135 + (i // 2) * 170
        d.node(x, y, 570, 145, "", "", white, DARK)
        d.label(x + 22, y + 44, p, ORANGE, 14)
        d.para(x + 22, y + 56, 520, "<b>%s</b>" % t, size=21)
        d.para(x + 22, y + 92, 520, s, size=14, color=GREY)


# ------------------------------------------------------------------ PART 1
@slide
def s_prereq(d):
    d.slide("Prerequisites", "Part 1 | Setup")
    rows = [["You need", "Version", "Check it works"],
            ["AWS account (billing enabled)", "-", "Sign in to the console"],
            ["AWS CLI", "v2", "<font name='Courier'>aws --version</font>"],
            ["Python", "3.9+ (Lambda runs 3.12)", "<font name='Courier'>python3 --version</font>"],
            ["Node.js (for the dashboard)", "20+", "<font name='Courier'>node -v</font>"],
            ["Git and GitHub CLI", "any recent", "<font name='Courier'>git --version</font>"],
            ["Gmail account (optional)", "-", "Needed only for tasks-from-email and calendar"]]
    y = d.table(56, 130, [400, 300, 468], rows, size=16)
    d.callout(56, y + 35, 570, "Why", "Use an <b>IAM user</b> (or SSO), not the root account, and turn on <b>MFA</b>. The CLI needs credentials to create resources for you.", ORANGE)
    d.callout(654, y + 35, 570, "Expected result", "Each check prints a version number. If a command is \"not found\", install that tool first and re-check.", GREEN)
    d.callout(56, y + 150, 1168, "Warning", "Never paste access keys into chats, code, screenshots or Git. If a key leaks, deactivate it in IAM immediately and create a new one.", RED)


@slide
def s_cli(d):
    d.slide("Step 1: connect the AWS CLI", "Part 1 | Setup")
    d.code(56, 130, 620, [
        "$ aws configure",
        "# AWS Access Key ID: <your key>",
        "# AWS Secret Access Key: <your secret>",
        "# Default region name: us-east-1",
        "# Default output format: json",
        "",
        "$ aws sts get-caller-identity",
        "= {",
        "=   \"Account\": \"123456789012\",",
        "=   \"Arn\": \"arn:aws:iam::123456789012:user/you\"",
        "= }"], size=13, title="terminal")
    d.callout(56, 440, 620, "Why", "Every later command (deploy, logs, tests) talks to your account through these credentials. <b>get-caller-identity</b> proves they work.")
    d.callout(56, 560, 620, "Expected result", "Your 12-digit account number and user ARN. An error means the keys or region are wrong.", GREEN)
    d.para(716, 130, 508, "Tip: <b>us-east-1</b> is used throughout because every service here (and Cost Explorer) is available there.", size=14, color=GREY)


@slide
def s_bedrock(d):
    d.slide("Step 2: enable an Amazon Bedrock model", "Part 1 | Setup")
    d.bullets(56, 130, 540, [
        "Console > <b>Amazon Bedrock</b> > <b>Model catalog</b>. Choose the region (us-east-1).",
        "Pick a model. <b>Amazon Nova Lite</b> is cheap and usually works immediately. Anthropic models may ask for a one-time use-case form.",
        "New models need an <b>inference profile ID</b> with a region prefix: <font name='Courier'>us.</font> <font name='Courier'>apac.</font> <font name='Courier'>global.</font>",
        "Test it from the terminal before writing any code."], size=15, gap=10)
    d.code(626, 130, 598, [
        "$ aws bedrock list-inference-profiles \\",
        "    --region us-east-1 --query \\",
        "    'inferenceProfileSummaries[].inferenceProfileId'",
        "",
        "$ aws bedrock-runtime converse \\",
        "    --region us-east-1 \\",
        "    --model-id us.amazon.nova-lite-v1:0 \\",
        "    --messages '[{\"role\":\"user\",",
        "      \"content\":[{\"text\":\"Say hi\"}]}]'",
        "= {\"output\":{\"message\":{\"role\":\"assistant\",",
        "=   \"content\":[{\"text\":\"Hi there!\"}]}}, ...}"], size=12.5, title="terminal")
    d.callout(56, 470, 540, "Why", "The agent calls this exact API. If it fails here, it will fail in Lambda, so fix access now.")
    d.callout(626, 470, 598, "Common error", "<b>AccessDeniedException</b>: the model is not enabled for your account/region. <b>ValidationException: on-demand throughput isn't supported</b>: use an inference profile ID.", RED)


@slide
def s_repo(d):
    d.slide("Repository structure", "Part 1 | Setup")
    d.code(56, 125, 520, [
        "daily-briefing-weather-agent/",
        "  src/                  # the Lambda code",
        "    handler.py          # entry point",
        "    config.py           # env vars",
        "    utils.py            # JSON logs, HTTP",
        "    weather_client.py   # Open-Meteo",
        "    news_client.py      # AWS + Hacker News",
        "    calendar_client.py  # Google iCal",
        "    tasks_client.py     # Gmail -> tasks",
        "    billing_client.py   # Cost Explorer",
        "    bedrock_client.py   # Converse API",
        "    briefing.py         # prompt + logic",
        "    notifier.py         # SNS publish",
        "    remote_settings.py  # SSM overrides",
        "    run_store.py        # DynamoDB history",
        "  tests/  local_run.py  requirements.txt",
        "  iam/  scripts/  .github/workflows/",
        "  frontend/             # Next.js dashboard"], size=12, title="layout")
    rows = [["File", "Single responsibility"],
            ["handler.py", "Lambda entry: orchestrates a run, records the result"],
            ["bedrock_client.py", "Only talks to Bedrock"],
            ["weather_client.py", "Only fetches weather"],
            ["briefing.py", "Builds the prompt, calls Bedrock, has the safe fallback"],
            ["notifier.py", "Only publishes to SNS"],
            ["config.py", "Reads every setting from environment variables"],
            ["utils.py", "Logging, timing, HTTP, the SourceResult type"]]
    d.table(610, 125, [190, 424], rows, size=13.5)
    d.callout(610, 470, 614, "Why this layout", "Each file does one job. Students can read, test or replace one part (say, swap the weather API) without touching the rest.", GREEN)


@slide
def s_env(d):
    d.slide("Configuration: environment variables", "Part 1 | Setup")
    rows = [["Variable", "Default", "Meaning"],
            ["CITY / TIMEZONE", "Indore / Asia/Kolkata", "Weather location; dates and schedule timezone"],
            ["BRIEFING_TOPICS", "weather,aws,tech,calendar,tasks,billing", "Which sections to include"],
            ["BEDROCK_REGION / MODEL_ID", "us-east-1 / us.amazon.nova-lite-v1:0", "Where and which model"],
            ["SNS_TOPIC_ARN", "(set by deploy)", "Where to publish the email"],
            ["GMAIL_USER / GMAIL_LABEL", "(empty) / INBOX", "Mailbox to scan for tasks; empty = off"],
            ["CALENDAR_ICS_URL", "(empty)", "Secret iCal address; empty = off"],
            ["USER_NAME", "(empty)", "Name in the greeting"],
            ["DRY_RUN", "false", "true = never publish to SNS"],
            ["HN_API_URL, WEATHER_URL, ...", "public endpoints", "Every API endpoint is configurable"]]
    y = d.table(56, 130, [330, 400, 438], rows, size=15, mono_cols=(0,))
    d.callout(56, y + 35, 570, "Why env vars", "Same code runs locally and in Lambda; only the configuration changes. No secrets are hard-coded.")
    d.callout(654, y + 35, 570, "Reserved name", "Lambda reserves <b>AWS_REGION</b>, so the Bedrock region is called <b>BEDROCK_REGION</b>.", AMBER)


@slide
def s_local_setup(d):
    d.slide("Step 3: set up the project locally", "Part 1 | Setup")
    d.code(56, 125, 700, [
        "$ git clone https://github.com/<you>/daily-briefing-weather-agent.git",
        "$ cd daily-briefing-weather-agent",
        "$ python3 -m venv .venv && source .venv/bin/activate",
        "$ pip install -r requirements.txt   # boto3: needed for billing + Bedrock",
        "",
        "$ python local_run.py --no-ai",
        "= ==========================================================",
        "= SUBJECT: Daily Briefing - Indore - 29 Sep 2026",
        "= [AI summary unavailable - showing raw data]",
        "= WEATHER  {\"city\": \"Indore\", \"temperature\": 31.9, ...}",
        "= AWS ANNOUNCEMENTS  - Claude Sonnet 5.5 now available ...",
        "= AI used: False | sources: {'weather': 'ok', ...}"], size=12.5, title="terminal")
    d.callout(780, 125, 444, "Why --no-ai", "It proves data collection works without Bedrock. Run it <b>inside the activated venv</b>: without boto3 the billing section shows unavailable. Add AI after this works.")
    d.callout(780, 265, 444, "Expected result", "A plain-text briefing built from live data. \"AI used: False\" is correct here.", GREEN)
    d.callout(780, 400, 444, "Dependencies", "Only <b>boto3</b> (already inside Lambda). Everything else uses the Python standard library, so the zip stays tiny.", ORANGE)
    d.para(56, 470, 700, "<b>requirements.txt</b>", size=15)
    d.code(56, 495, 700, ["boto3>=1.35   # AWS SDK (Bedrock, SNS, SSM, DynamoDB)"], size=12.5)
