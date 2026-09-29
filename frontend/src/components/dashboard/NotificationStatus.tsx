import { Mail } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Run } from "@/lib/types";
import { EmptyState, ErrorState, LoadingState } from "./states";
import { StatusBadge } from "./StatusBadge";

export function NotificationStatus({ run, loading, generating, nextLabel, error, onRetry }: { run?: Run; loading?: boolean; generating?: boolean; nextLabel?: string; error?: string; onRetry?: () => void }) {
  return (
    <Card aria-label="Delivery status">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base"><Mail className="size-4 text-primary" aria-hidden />Delivery</CardTitle>
        {generating ? <StatusBadge status="generating" /> : run ? <StatusBadge status={run.status} /> : null}
      </CardHeader>
      <CardContent aria-live="polite" className="space-y-2 text-sm">
        {loading ? <LoadingState lines={2} label="Loading delivery status" />
          : error ? <ErrorState message={error} onRetry={onRetry} />
          : !run ? <EmptyState title="Nothing sent yet" description="Delivery details appear after the first briefing." />
          : (
            <div className="animate-in fade-in space-y-2">
              <Row k="To" v={run.recipient} />
              <Row k="Sent" v={new Date(run.startedAt).toLocaleString("en-IN")} />
              {run.messageId && <Row k="Message ID" v={<code className="break-all text-xs">{run.messageId}</code>} />}
              {run.error && <p className={`rounded-[4px] p-2 text-xs ${run.status === "failed" ? "bg-destructive/10 text-destructive" : "bg-amber-50 text-amber-800"}`}>{run.error}</p>}
              {nextLabel && <Row k="Next" v={nextLabel} />}
            </div>
          )}
      </CardContent>
    </Card>
  );
}
const Row = ({ k, v }: { k: string; v: React.ReactNode }) => (<div className="flex justify-between gap-3"><span className="text-muted-foreground">{k}</span><span className="text-right font-medium">{v}</span></div>);
