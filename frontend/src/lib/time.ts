export const TIMEZONES = [
  "Asia/Kolkata", "Asia/Dubai", "Asia/Singapore", "Asia/Tokyo", "Europe/London",
  "Europe/Berlin", "America/New_York", "America/Chicago", "America/Los_Angeles", "Australia/Sydney", "UTC",
];

/** Next occurrence of HH:MM in `timeZone`, as an absolute Date. */
export function nextRunAt(time: string, timeZone: string, now: Date = new Date()): Date {
  const [h, m] = time.split(":").map(Number);
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone, hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
  }).formatToParts(now);
  const get = (t: string) => Number(parts.find((p) => p.type === t)?.value ?? 0);
  const nowSec = get("hour") * 3600 + get("minute") * 60 + get("second");
  let delta = h * 3600 + m * 60 - nowSec;
  if (delta <= 0) delta += 86400;
  return new Date(now.getTime() + delta * 1000);
}

export function formatDateTime(iso: string | Date, timeZone: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    timeZone, weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: true,
  }).format(new Date(iso));
}

export function formatCountdown(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

export function formatDuration(ms: number): string {
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
}
