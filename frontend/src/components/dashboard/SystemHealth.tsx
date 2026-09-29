import { Activity, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { HealthState, ServiceHealth } from "@/lib/types";
import { ErrorState, LoadingState } from "./states";

const DOT: Record<HealthState, { cls: string; label: string }> = {
  operational: { cls: "bg-success", label: "Operational" },
  degraded: { cls: "bg-amber-500", label: "Degraded" },
  down: { cls: "bg-destructive", label: "Down" },
};

export function SystemHealth({ services, loading, error, onRefresh }: { services?: ServiceHealth[]; loading?: boolean; error?: string; onRefresh: () => void }) {
  return (
    <Card aria-label="System health">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base"><Activity className="size-4 text-primary" aria-hidden />System health</CardTitle>
        <Button variant="ghost" size="icon" onClick={onRefresh} aria-label="Refresh system health"><RefreshCw className={loading ? "animate-spin" : ""} /></Button>
      </CardHeader>
      <CardContent>
        {error ? <ErrorState message={error} onRetry={onRefresh} /> : loading && !services ? <LoadingState lines={4} label="Checking services" /> : (
          <ul className="divide-y">
            {services?.map((s) => (
              <li key={s.id} className="flex items-center justify-between py-2 text-sm">
                <span className="flex items-center gap-2"><span className={`size-2.5 rounded-full ${DOT[s.state].cls}`} aria-hidden />{s.name}</span>
                <span className="text-xs text-muted-foreground"><span className="sr-only">{DOT[s.state].label}: </span>{s.detail}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
