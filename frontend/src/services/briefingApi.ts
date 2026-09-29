/**
 * Typed API layer: the UI only talks to these functions.
 * Everything here is REAL. Requests go to this app's own server routes (src/app/api/*), which run
 * on the server with your local AWS credentials. The browser never sees AWS keys.
 *
 *   /api/settings  -> EventBridge Scheduler + SSM Parameter Store + SNS
 *   /api/generate  -> invokes the Lambda (real email)
 *   /api/runs      -> run history from DynamoDB (written by the Lambda)
 *   /api/health    -> live checks of the five services
 * City search and weather use the free Open-Meteo API (no key needed).
 */
import type { Briefing, Location, Run, ServiceHealth, Settings, StepId, Weather } from "@/lib/types";

async function call<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { ...init, headers: { "Content-Type": "application/json" }, cache: "no-store" });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error ?? `Request failed (${res.status})`);
  return data as T;
}

export const getSettings = () => call<Settings>("/api/settings");
export const saveSettings = (next: Settings) => call<Settings>("/api/settings", { method: "PUT", body: JSON.stringify(next) });
export async function setScheduleEnabled(enabled: boolean) {
  return saveSettings({ ...(await getSettings()), enabled });
}
export const getHistory = () => call<Run[]>("/api/runs");
export const getSystemHealth = () => call<ServiceHealth[]>("/api/health");
export async function getLatestBriefing(): Promise<Briefing | null> {
  return (await getHistory()).find((r) => r.briefing)?.briefing ?? null;
}

export async function searchCities(query: string, signal?: AbortSignal): Promise<Location[]> {
  const q = query.trim();
  if (q.length < 2) return [];
  const res = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=8&language=en&format=json`, { signal });
  if (!res.ok) throw new Error("City search is unavailable right now");
  const data = await res.json();
  return (data.results ?? []).map((r: Record<string, unknown>) => ({
    name: r.name as string, country: (r.country as string) ?? "", admin1: r.admin1 as string | undefined,
    latitude: r.latitude as number, longitude: r.longitude as number, timezone: (r.timezone as string) ?? "UTC",
  }));
}

const WMO: Record<number, [Weather["condition"], string]> = {
  0: ["clear", "Clear sky"], 1: ["clear", "Mainly clear"], 2: ["partly", "Partly cloudy"], 3: ["cloudy", "Overcast"],
  45: ["cloudy", "Fog"], 48: ["cloudy", "Fog"], 51: ["rain", "Light drizzle"], 53: ["rain", "Drizzle"], 55: ["rain", "Heavy drizzle"],
  61: ["rain", "Light rain"], 63: ["rain", "Rain"], 65: ["rain", "Heavy rain"], 80: ["rain", "Rain showers"], 81: ["rain", "Rain showers"],
  82: ["rain", "Violent showers"], 95: ["storm", "Thunderstorm"], 96: ["storm", "Thunderstorm"], 99: ["storm", "Thunderstorm"],
};

export async function getWeather(loc: Location): Promise<Weather> {
  const url = "https://api.open-meteo.com/v1/forecast?latitude=" + loc.latitude + "&longitude=" + loc.longitude +
    "&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m" +
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto&forecast_days=1";
  const res = await fetch(url);
  if (!res.ok) throw new Error("Weather service did not respond");
  const w = await res.json();
  const [condition, label] = WMO[w.current.weather_code] ?? ["cloudy", "Cloudy"];
  return {
    city: loc.name, country: loc.country, temperature: w.current.temperature_2m, feelsLike: w.current.apparent_temperature,
    condition, conditionLabel: label, humidity: w.current.relative_humidity_2m, windKmh: w.current.wind_speed_10m,
    high: Math.round(w.daily.temperature_2m_max[0]), low: Math.round(w.daily.temperature_2m_min[0]),
    rainChance: w.daily.precipitation_probability_max[0] ?? 0, observedAt: w.current.time, status: "ok",
  };
}

/** What the Lambda run really did, as diagram step states. */
export function stepsFromRun(run: Run): Record<StepId, "idle" | "running" | "done" | "failed"> {
  const src = run.sources ?? {};
  const failed = run.status === "failed";
  const weather = src.weather ? (src.weather === "ok" ? "done" : "failed") : failed ? "idle" : "done";
  return {
    scheduler: run.trigger === "scheduled" ? "done" : "idle", lambda: failed ? "failed" : "done", weather,
    bedrock: failed ? "idle" : run.aiUsed === false ? "failed" : "done",
    sns: failed ? "idle" : run.sent ? "done" : "idle", user: run.sent ? "done" : "idle",
  };
}

/** Runs the real Lambda once. `onRunning` fires while it works. Throws (with `.run`) on failure. */
export async function generateBriefing(onRunning: () => void): Promise<Run> {
  onRunning();
  try {
    await call("/api/generate", { method: "POST", body: "{}" });
  } catch (e) {
    const runs = await getHistory().catch(() => []);
    throw Object.assign(e as Error, { run: runs[0] });
  }
  const run = (await getHistory())[0];
  if (!run) throw new Error("The run finished but no history record was found");
  return run;
}
