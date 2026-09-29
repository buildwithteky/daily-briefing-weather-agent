export type TopicId = "weather" | "aws" | "tech" | "calendar" | "tasks" | "billing";
export type RunStatus = "delivered" | "partial" | "generated" | "failed" | "generating" | "scheduled";
export type SourceStatus = "ok" | "stale" | "unavailable";
export type HealthState = "operational" | "degraded" | "down";
export type StepId = "scheduler" | "lambda" | "weather" | "bedrock" | "sns" | "user";
export type StepState = "idle" | "running" | "done" | "failed";

export interface Location {
  name: string;
  country: string;
  admin1?: string; // state / region
  latitude: number;
  longitude: number;
  timezone: string; // IANA, e.g. Asia/Kolkata
}

export interface Settings {
  userName: string; // used in the greeting
  city: string;
  location: Location; // the place picked in the city search
  timezone: string;
  time: string; // "HH:MM" 24h, in `timezone`
  email: string;
  topics: TopicId[];
  enabled: boolean;
  notifyOnSuccess: boolean;
  notifyOnFailure: boolean;
}

export interface Weather {
  city: string;
  country: string;
  temperature: number;
  feelsLike: number;
  condition: "clear" | "cloudy" | "rain" | "storm" | "partly";
  conditionLabel: string;
  humidity: number;
  windKmh: number;
  high: number;
  low: number;
  rainChance: number;
  observedAt: string; // ISO
  status: SourceStatus;
}

export interface BriefingSection {
  id: "weather" | "aws" | "tech" | "tasks" | "summary";
  title: string;
  status: SourceStatus;
  items: string[]; // bullet lines; for `summary` a single paragraph
}

export interface Briefing {
  id: string;
  generatedAt: string;
  subject: string;
  sections: BriefingSection[];
}

export interface Run {
  id: string;
  startedAt: string;
  status: RunStatus;
  durationMs: number;
  trigger: "scheduled" | "manual";
  recipient: string;
  messageId?: string;
  error?: string;
  sources?: Record<string, string>; // per-source status of that run
  aiUsed?: boolean;
  sent?: boolean;
  briefing?: Briefing;
}

export interface ServiceHealth {
  id: "bedrock" | "lambda" | "scheduler" | "sns" | "weather";
  name: string;
  state: HealthState;
  detail: string;
}
