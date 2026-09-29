"use client";
import { useEffect, useState } from "react";
import { CalendarClock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import type { Settings } from "@/lib/types";
import { formatCountdown, formatDateTime, nextRunAt } from "@/lib/time";
import { LoadingState } from "./states";

interface Props { settings?: Settings; loading?: boolean; toggling?: boolean; onToggle: (enabled: boolean) => void }

export function ScheduleCard({ settings, loading, toggling, onToggle }: Props) {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    const tick = () => setNow(new Date());
    const first = setTimeout(tick, 0); // client-only clock avoids a hydration mismatch
    const t = setInterval(tick, 1000);
    return () => { clearTimeout(first); clearInterval(t); };
  }, []);

  const next = settings && now ? nextRunAt(settings.time, settings.timezone, now) : null;
  return (
    <Card aria-label="Next briefing">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base"><CalendarClock className="size-4 text-primary" aria-hidden />Next briefing</CardTitle>
        {settings && <Badge variant="outline" className="rounded-[4px]">{settings.enabled ? "Active" : "Paused"}</Badge>}
      </CardHeader>
      <CardContent className="space-y-4">
        {loading || !settings ? <LoadingState lines={2} label="Loading schedule" /> : (
          <>
            {settings.enabled && next ? (
              <div className="animate-in fade-in">
                <p className="font-mono text-3xl font-medium tabular-nums" aria-live="off">{formatCountdown(next.getTime() - now!.getTime())}</p>
                <p className="mt-1 text-sm text-muted-foreground">{formatDateTime(next, settings.timezone)} ({settings.timezone})</p>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">The schedule is paused. Turn it on to receive your briefing automatically every day at {settings.time}.</p>
            )}
            <label className="flex items-center justify-between gap-3 border-t pt-3 text-sm font-medium">
              Daily automation
              <Switch checked={settings.enabled} disabled={toggling} onCheckedChange={onToggle} aria-label="Enable daily automated briefing" />
            </label>
          </>
        )}
      </CardContent>
    </Card>
  );
}
