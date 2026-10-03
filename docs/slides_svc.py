from tutorial_lib import *

S = []
ICONS = {"Amazon EventBridge Scheduler": "eventbridge", "AWS Lambda": "lambda", "Amazon Bedrock": "bedrock", "Amazon SNS": "sns",
         "AWS IAM": "iam", "Amazon DynamoDB": "dynamodb", "AWS Systems Manager Parameter Store": "ssm",
         "Amazon CloudWatch": "cloudwatch", "AWS Cost Explorer": "costexplorer"}
STAGES = ["EventBridge", "Lambda", "Data sources", "Bedrock", "SNS", "Your inbox"]


def svc(d, title, tagline, stages, what, analogy, uses, settings, where, watch, cost):
    d.slide(title, "AWS services explained")
    d.para(56, 96, 1090, tagline, size=17, color=GREY)
    if title in ICONS:
        d.icon(ICONS[title], 1224 - 64, 24, 64)
    # where it sits in the pipeline
    d.label(56, 152, "Where it sits", GREY, 11)
    x = 170
    for i, s in enumerate(STAGES):
        hot = i in stages
        x = d.chip(x, 136, s, fill=ORANGE if hot else SOFT, color=white if hot else GREY, size=12)
    # three columns
    d.label(56, 200, "What it is", ORANGE, 12)
    h = d.para(56, 214, 384, what, size=17, leading=23)
    d.callout(56, 214 + h + 18, 384, "Think of it as", analogy, GREEN, size=15.5)
    d.label(470, 200, "How this project uses it", ORANGE, 12)
    d.bullets(470, 214, 390, uses, size=16, gap=11)
    d.label(890, 200, "Key settings used", ORANGE, 12)
    y = d.table(890, 214, [120, 214], [["Setting", "Value"]] + settings, size=13.5)
    d.para(890, y + 12, 334, "Console: " + where, size=13, color=GREY)
    d.callout(56, 540, 570, "Watch out", watch, AMBER, size=14.5)
    d.callout(654, 540, 570, "Cost", cost, GREY, size=14.5)


def slide(f): S.append(f); return f


@slide
def eb(d):
    svc(d, "Amazon EventBridge Scheduler", "The alarm clock that starts the agent every morning, with no server running in between.",
        [0],
        "A managed scheduler. You give it a time rule (a cron expression, a fixed rate, or a one-off time), a timezone, and a <b>target</b>. At the right moment it calls the target for you. It can call over 270 AWS services, including Lambda.",
        "An alarm clock in the cloud that never sleeps in and never needs charging.",
        ["One schedule, <font name='Courier'>daily-briefing-9am</font>, fires every day at 09:00 in Asia/Kolkata",
         "Its target is the Lambda function; it passes <font name='Courier'>{\"source\":\"eventbridge-scheduler\"}</font> so the run is labelled \"scheduled\"",
         "It assumes the <b>Scheduler role</b>, which may invoke only this Lambda",
         "The dashboard changes the time and the on/off switch with <b>UpdateSchedule</b>"],
        [["Expression", "cron(0 9 * * ? *)"], ["Timezone", "Asia/Kolkata"], ["Flexible window", "OFF (exact time)"], ["State", "ENABLED / DISABLED"], ["Target", "Lambda ARN + role ARN"]],
        "EventBridge > Scheduler > Schedules",
        "UpdateSchedule <b>replaces the whole schedule</b>, so the target and role must be sent again on every update. Without the role, nothing fires.",
        "Free for the first 14 million invocations a month. One run a day is 30.")


@slide
def lam(d):
    svc(d, "AWS Lambda", "Runs the Python agent on demand. Nothing to patch, nothing to keep running.",
        [1],
        "A serverless compute service. You upload code and Lambda runs it whenever something triggers it, then shuts it down. You pay only for the milliseconds the code runs. One run can last up to 15 minutes.",
        "A chef who is hired only when an order arrives and is paid by the minute.",
        ["Runs <font name='Courier'>src.handler.lambda_handler</font> on Python 3.12",
         "Reads settings from environment variables and the dashboard's saved settings",
         "Calls six data sources, then Bedrock, then SNS; saves the run; logs every step",
         "Uses an <b>execution role</b> instead of any stored AWS key"],
        [["Runtime", "python3.12"], ["Handler", "src.handler.lambda_handler"], ["Timeout", "60 s"], ["Memory", "256 MB"], ["Network", "no VPC (public internet)"]],
        "Lambda > Functions > daily-briefing-agent",
        "Keep the timeout longer than your slowest run (12 to 30 s here). <b>AWS_REGION is reserved</b>, hence BEDROCK_REGION. Inside a VPC you would need a paid NAT gateway to reach the APIs.",
        "Free tier: 1M requests and 400,000 GB-seconds a month. This project stays inside it.")


@slide
def bed(d):
    svc(d, "Amazon Bedrock", "The AI brain: writes the briefing and pulls tasks out of your email.",
        [3],
        "A managed service for foundation models from several providers (Amazon Nova, Anthropic Claude and others) behind one API. No GPUs to rent and no model to host. Your prompts stay in your AWS account.",
        "A very fast writer on call, paid by the word.",
        ["<b>Call 1:</b> turns the collected data into the briefing text",
         "<b>Call 2:</b> reads recent email snippets and returns a short JSON list of tasks",
         "Uses the <b>Converse API</b>, so changing model means changing one variable",
         "Prompts tell the model to use only the given data and to say \"unavailable\" when data is missing"],
        [["Model", "us.amazon.nova-lite-v1:0"], ["Region", "us-east-1"], ["maxTokens", "800"], ["temperature", "0.3"], ["Permission", "bedrock:InvokeModel"]],
        "Amazon Bedrock > Model catalog",
        "The model must be enabled for your account and region. Newer models need an <b>inference profile ID</b> (us. / apac. / global. prefix), not a raw model ID.",
        "Billed per input and output token. A run uses a few thousand tokens: cents a month with a small model.")


@slide
def sns(d):
    svc(d, "Amazon SNS", "Delivers the finished briefing to your inbox.",
        [4, 5],
        "A publish and subscribe messaging service. A sender <b>publishes</b> one message to a <b>topic</b>, and SNS delivers it to every <b>subscriber</b> (email, SMS, another Lambda, a queue and more).",
        "A mailing list: write once, everyone subscribed gets a copy.",
        ["Topic <font name='Courier'>daily-briefing</font> with one <b>email subscription</b> (you)",
         "The Lambda publishes the subject and the body; SNS sends the email",
         "A failed run publishes a short \"Daily Briefing FAILED\" alert to the same topic",
         "Add more people by adding more subscriptions"],
        [["Topic", "daily-briefing"], ["Protocol", "email"], ["Endpoint", "your address"], ["Subject", "max 100 chars"], ["Permission", "sns:Publish (topic only)"]],
        "Amazon SNS > Topics > daily-briefing",
        "Email only works after the recipient clicks <b>Confirm subscription</b>. Mail comes from an AWS address, so check spam the first time. Body is plain text.",
        "First 1,000 email notifications a month are free. This project sends about 30.")


@slide
def iam(d):
    svc(d, "AWS IAM", "Decides who and what is allowed to do anything in your account.",
        [0, 1, 3, 4],
        "Identity and Access Management. <b>Roles</b> are identities that services can assume. A <b>trust policy</b> says who may assume a role; a <b>permission policy</b> says what the role may do. The safe rule is <b>least privilege</b>: grant only what is needed.",
        "Key cards that open only the doors each person or program needs.",
        ["<b>Lambda role:</b> invoke Bedrock, publish to one SNS topic, read two SSM parameters, write one DynamoDB table, read cost data, write logs",
         "<b>Scheduler role:</b> invoke this one Lambda, nothing else",
         "<b>GitHub deploy role:</b> assumed through OIDC, only by the repo's main branch",
         "No AWS key is stored in code, Lambda or GitHub"],
        [["Trust: Lambda role", "lambda.amazonaws.com"], ["Trust: Scheduler role", "scheduler.amazonaws.com"], ["Trust: CI role", "GitHub OIDC token"], ["Logs policy", "AWS-managed (basic execution)"], ["Custom policies", "iam/*.json"]],
        "IAM > Roles",
        "Only Cost Explorer needs <font name='Courier'>Resource: \"*\"</font>. Any key that appears in a chat, screenshot or Git must be rotated at once.",
        "IAM is free.")


@slide
def ddb(d):
    svc(d, "Amazon DynamoDB", "Remembers every run, so the dashboard can show real history.",
        [1],
        "A serverless NoSQL database that stores items looked up by key, with single-digit millisecond speed. There are no servers, no patching and no capacity planning in on-demand mode.",
        "A filing cabinet that adds drawers by itself when it fills up.",
        ["Table <font name='Courier'>daily-briefing-runs</font>: one item per run",
         "Each item holds status, trigger, duration, per-source status and the briefing text",
         "The dashboard queries the newest 20 items for the history and preview",
         "Items delete themselves after <b>30 days</b> (TTL)"],
        [["Partition key", "pk (always \"RUN\")"], ["Sort key", "startedAt (ISO time)"], ["Billing mode", "PAY_PER_REQUEST"], ["TTL attribute", "ttl (epoch seconds)"], ["Permission", "PutItem (Lambda)"]],
        "DynamoDB > Tables > daily-briefing-runs",
        "TTL deletion is not instant (it can take up to a couple of days). One item is limited to 400 KB, so the body is truncated. Saving history never blocks the email.",
        "On-demand: pay per read and write. 30 tiny items a month cost almost nothing.")


@slide
def ssm(d):
    svc(d, "AWS Systems Manager Parameter Store", "Keeps configuration and the Gmail password out of your code.",
        [1],
        "A central place for configuration values and secrets. A <b>String</b> parameter holds plain config; a <b>SecureString</b> is encrypted with AWS KMS and can only be read by identities you allow.",
        "A locked notice board that only certain people can read.",
        ["<font name='Courier'>/daily-briefing/gmail-app-password</font> (SecureString): the IMAP app password",
         "<font name='Courier'>/daily-briefing/settings</font> (String, JSON): city, timezone, topics, name, notification flags saved by the dashboard",
         "The Lambda reads both at the start of each run, so changes apply on the next run",
         "Only an allow-list of settings keys is honoured; bad values are ignored"],
        [["Secret type", "SecureString"], ["Settings type", "String (JSON)"], ["Read permission", "ssm:GetParameter"], ["Write permission", "dashboard user only"], ["Scope", "two parameter ARNs"]],
        "Systems Manager > Parameter Store",
        "Grant access per parameter ARN, never <font name='Courier'>*</font>. Never store a secret as a plain String. Type the password only in your own terminal.",
        "Standard parameters are free.")


@slide
def cw(d):
    svc(d, "Amazon CloudWatch", "The flight recorder: logs and metrics for every run, with no setup.",
        [1],
        "Lambda sends everything it prints to <b>CloudWatch Logs</b> automatically. <b>Logs Insights</b> lets you search and count log lines. <b>Metrics</b> (Invocations, Errors, Duration) can drive <b>alarms</b>.",
        "The black box in an aircraft: you open it when something went wrong.",
        ["Log group <font name='Courier'>/aws/lambda/daily-briefing-agent</font>",
         "One JSON line per step: scheduler.invoked, data.*, bedrock.*, sns.*, run.success",
         "Read live with <font name='Courier'>aws logs tail</font> or query with Logs Insights",
         "Secrets such as the calendar link and passwords are never logged"],
        [["Log group", "/aws/lambda/daily-briefing-agent"], ["Permission", "AWSLambdaBasicExecutionRole"], ["Retention", "never expires by default"], ["Useful metrics", "Errors, Duration"], ["Alarm (advice)", "Errors >= 1"]],
        "CloudWatch > Log groups",
        "By default logs are kept forever. Set <b>30 days</b> retention and add an alarm on Lambda Errors; deploy.sh does not create them.",
        "Charged per GB ingested and stored. These logs are tiny: cents.")


@slide
def ce(d):
    svc(d, "AWS Cost Explorer", "Where the billing section of your email comes from.",
        [2],
        "AWS's cost and usage analysis tool, also available as an API. It reports what you spent, by service and by day, shows credits, and forecasts the rest of the month.",
        "Your AWS bank statement, readable by code.",
        ["Asks for month-to-date usage grouped by service, excluding credits and refunds",
         "Asks separately for credits applied, so the net charge is exact",
         "Adds yesterday's usage and a month-end forecast when enough history exists",
         "The email shows only the figures, in a fixed bullet format"],
        [["API endpoint", "us-east-1"], ["Calls", "GetCostAndUsage, GetCostForecast"], ["Metric", "UnblendedCost"], ["Permission", "ce:* read, Resource *"], ["Prerequisite", "enable Cost Explorer"]],
        "Billing and Cost Management > Cost Explorer",
        "Enable it once in the console; data appears within about 24 hours and can lag by a day. The remaining credit balance has no API.",
        "About $0.01 per API request, roughly 4 per run: around $1.20 a month.")


S_ALL = S
