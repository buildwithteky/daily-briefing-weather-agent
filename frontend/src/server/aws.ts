/**
 * SERVER-ONLY AWS access (used by Next.js route handlers, never bundled for the browser).
 * Credentials come from the standard AWS chain on the machine running `next` (env vars or
 * ~/.aws/credentials). They are never sent to the browser.
 */
import { LambdaClient, GetFunctionConfigurationCommand, InvokeCommand } from "@aws-sdk/client-lambda";
import { GetScheduleCommand, SchedulerClient, UpdateScheduleCommand } from "@aws-sdk/client-scheduler";
import { GetParameterCommand, PutParameterCommand, SSMClient } from "@aws-sdk/client-ssm";
import { DynamoDBClient, QueryCommand } from "@aws-sdk/client-dynamodb";
import { ListSubscriptionsByTopicCommand, SNSClient, SubscribeCommand } from "@aws-sdk/client-sns";
import type { Location, Run, ServiceHealth, Settings, TopicId } from "@/lib/types";

const region = process.env.AWS_REGION || "us-east-1";
const FN = process.env.BRIEFING_FUNCTION_NAME || "daily-briefing-agent";
const SCHEDULE = process.env.BRIEFING_SCHEDULE_NAME || "daily-briefing-9am";
const TOPIC = process.env.BRIEFING_TOPIC_NAME || "daily-briefing";
const PARAM = process.env.BRIEFING_SETTINGS_PARAM || "/daily-briefing/settings";

const lambda = new LambdaClient({ region });
const scheduler = new SchedulerClient({ region });
const ssm = new SSMClient({ region });
const sns = new SNSClient({ region });
const ddb = new DynamoDBClient({ region });
const RUNS_TABLE = process.env.BRIEFING_RUNS_TABLE || "daily-briefing-runs";

const TOPICS: TopicId[] = ["weather", "aws", "tech", "calendar", "tasks", "billing"];
export class ValidationError extends Error {}

async function topicArn(): Promise<string> {
  const cfg = await lambda.send(new GetFunctionConfigurationCommand({ FunctionName: FN }));
  const account = cfg.FunctionArn!.split(":")[4];
  return `arn:aws:sns:${region}:${account}:${TOPIC}`;
}

async function geocode(city: string): Promise<Location> {
  const r = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&format=json`);
  const d = (await r.json()).results?.[0];
  if (!d) throw new ValidationError(`City not found: ${city}`);
  return { name: d.name, country: d.country ?? "", admin1: d.admin1, latitude: d.latitude, longitude: d.longitude, timezone: d.timezone ?? "UTC" };
}

export async function getSettings(): Promise<Settings> {
  const [sched, cfg, arn] = await Promise.all([
    scheduler.send(new GetScheduleCommand({ Name: SCHEDULE })),
    lambda.send(new GetFunctionConfigurationCommand({ FunctionName: FN })),
    topicArn(),
  ]);
  const m = /cron\((\d+) (\d+) /.exec(sched.ScheduleExpression ?? "");
  const time = m ? `${m[2].padStart(2, "0")}:${m[1].padStart(2, "0")}` : "09:00";

  let saved: Partial<Settings> = {};
  try {
    saved = JSON.parse((await ssm.send(new GetParameterCommand({ Name: PARAM }))).Parameter!.Value!);
  } catch { /* nothing saved yet: fall back to Lambda environment */ }

  const env = cfg.Environment?.Variables ?? {};
  const city = saved.city ?? env.CITY ?? "Indore";
  const subs = await sns.send(new ListSubscriptionsByTopicCommand({ TopicArn: arn }));
  const email = subs.Subscriptions?.find((s) => s.Protocol === "email")?.Endpoint ?? "";
  return {
    userName: saved.userName ?? env.USER_NAME ?? "", city, location: saved.location ?? (await geocode(city)),
    timezone: sched.ScheduleExpressionTimezone ?? saved.timezone ?? env.TIMEZONE ?? "Asia/Kolkata", time,
    email, topics: saved.topics ?? ((env.BRIEFING_TOPICS ?? "weather").split(",") as TopicId[]),
    enabled: sched.State === "ENABLED", notifyOnSuccess: saved.notifyOnSuccess ?? true, notifyOnFailure: saved.notifyOnFailure ?? true,
  };
}

function validate(s: Settings) {
  if ((s.userName ?? "").length > 40) throw new ValidationError("Name is too long (max 40)");
  if (!s.city?.trim() || s.city.length > 80) throw new ValidationError("City is required");
  if (!/^\d{2}:\d{2}$/.test(s.time)) throw new ValidationError("Time must be HH:MM");
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s.email)) throw new ValidationError("Invalid email");
  if (!Array.isArray(s.topics) || !s.topics.length || s.topics.some((t) => !TOPICS.includes(t))) throw new ValidationError("Invalid topics");
  try { new Intl.DateTimeFormat("en", { timeZone: s.timezone }); } catch { throw new ValidationError("Invalid timezone"); }
}

export async function putSettings(s: Settings): Promise<Settings> {
  validate(s);
  const before = await getSettings();

  // 1) what the Lambda reads on every run
  await ssm.send(new PutParameterCommand({
    Name: PARAM, Type: "String", Overwrite: true,
    Value: JSON.stringify({ userName: (s.userName ?? "").trim(), city: s.city.trim(), timezone: s.timezone, topics: s.topics, location: s.location, notifyOnSuccess: s.notifyOnSuccess, notifyOnFailure: s.notifyOnFailure }),
  }));

  // 2) EventBridge schedule: time, timezone, enabled (UpdateSchedule replaces the whole schedule, so re-send the target)
  const cur = await scheduler.send(new GetScheduleCommand({ Name: SCHEDULE }));
  const [h, m] = s.time.split(":").map(Number);
  await scheduler.send(new UpdateScheduleCommand({
    Name: SCHEDULE, GroupName: cur.GroupName, FlexibleTimeWindow: cur.FlexibleTimeWindow, Target: cur.Target,
    ScheduleExpression: `cron(${m} ${h} * * ? *)`, ScheduleExpressionTimezone: s.timezone,
    State: s.enabled ? "ENABLED" : "DISABLED", Description: cur.Description,
  }));

  // 3) new email address -> SNS subscription (AWS sends a confirmation mail)
  if (s.email.toLowerCase() !== before.email.toLowerCase()) {
    await sns.send(new SubscribeCommand({ TopicArn: await topicArn(), Protocol: "email", Endpoint: s.email }));
  }
  return getSettings();
}

export async function generateNow() {
  const res = await lambda.send(new InvokeCommand({
    FunctionName: FN, InvocationType: "RequestResponse", Payload: new TextEncoder().encode(JSON.stringify({ source: "dashboard" })),
  }));
  const text = new TextDecoder().decode(res.Payload);
  if (res.FunctionError) throw new Error(`Lambda failed: ${(JSON.parse(text).errorMessage as string) ?? res.FunctionError}`);
  return JSON.parse(text) as { message_id: string; ai_used: boolean; sources: Record<string, string>; subject: string; body: string; duration_ms: number };
}

/* ------------------------------ run history ------------------------------ */
export async function listRuns(limit = 20): Promise<Run[]> {
  const [res, settings] = await Promise.all([
    ddb.send(new QueryCommand({ TableName: RUNS_TABLE, KeyConditionExpression: "pk = :p", ExpressionAttributeValues: { ":p": { S: "RUN" } }, ScanIndexForward: false, Limit: limit })),
    getSettings().catch(() => undefined),
  ]);
  return (res.Items ?? []).map((i) => {
    const body = i.body?.S;
    const started = i.startedAt.S!;
    return {
      id: started, startedAt: started, status: i.status.S as Run["status"], durationMs: Number(i.durationMs?.N ?? 0),
      trigger: (i.trigger?.S as Run["trigger"]) ?? "manual", recipient: settings?.email ?? "", messageId: i.messageId?.S,
      error: i.error?.S, sources: i.sources?.S ? JSON.parse(i.sources.S) : undefined, aiUsed: i.aiUsed?.BOOL, sent: i.sent?.BOOL,
      briefing: body ? { id: started, generatedAt: started, subject: i.subject?.S ?? "Briefing", sections: [{ id: "summary" as const, title: i.subject?.S ?? "Briefing", status: "ok" as const, items: [body] }] } : undefined,
    };
  });
}

/* ------------------------------ system health ---------------------------- */
async function timed<T>(fn: () => Promise<T>): Promise<[T, number]> {
  const t = Date.now();
  const v = await fn();
  return [v, Date.now() - t];
}

export async function checkHealth(): Promise<ServiceHealth[]> {
  const out: ServiceHealth[] = [];
  const add = async (id: ServiceHealth["id"], name: string, fn: () => Promise<Pick<ServiceHealth, "state" | "detail">>) => {
    try { out.push({ id, name, ...(await fn()) }); }
    catch (e) { out.push({ id, name, state: "down", detail: (e as Error).name || "Check failed" }); }
  };
  const runs = await listRuns(1).catch(() => [] as Run[]);
  const last = runs[0];

  await Promise.all([
    add("scheduler", "EventBridge Scheduler", async () => {
      const s = await scheduler.send(new GetScheduleCommand({ Name: SCHEDULE }));
      return s.State === "ENABLED" ? { state: "operational", detail: "Schedule enabled" } : { state: "degraded", detail: "Schedule paused" };
    }),
    add("lambda", "AWS Lambda", async () => {
      const c = await lambda.send(new GetFunctionConfigurationCommand({ FunctionName: FN }));
      if (c.State !== "Active") return { state: "down", detail: `Function ${c.State}` };
      if (!last) return { state: "operational", detail: "Ready, no runs yet" };
      return last.status === "failed" ? { state: "degraded", detail: "Last run failed" } : { state: "operational", detail: "Last run OK" };
    }),
    add("weather", "Weather API", async () => {
      const [r, ms] = await timed(() => fetch("https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&current=temperature_2m", { signal: AbortSignal.timeout(5000) }));
      return r.ok ? { state: "operational", detail: `Responding (${ms} ms)` } : { state: "down", detail: `HTTP ${r.status}` };
    }),
    add("bedrock", "Amazon Bedrock", async () => {
      if (!last) return { state: "operational", detail: "No runs yet" };
      if (last.status === "failed") return { state: "degraded", detail: "Last run failed" };
      return last.aiUsed === false ? { state: "degraded", detail: "Last run used fallback" } : { state: "operational", detail: "Last summary OK" };
    }),
    add("sns", "Amazon SNS", async () => {
      const subs = await sns.send(new ListSubscriptionsByTopicCommand({ TopicArn: await topicArn() }));
      const emails = subs.Subscriptions?.filter((x) => x.Protocol === "email") ?? [];
      if (!emails.length) return { state: "down", detail: "No email subscription" };
      return emails.some((x) => x.SubscriptionArn?.startsWith("arn:")) ? { state: "operational", detail: "Email confirmed" } : { state: "degraded", detail: "Confirm the subscription email" };
    }),
  ]);
  const order = ["scheduler", "lambda", "weather", "bedrock", "sns"];
  return out.sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
}
