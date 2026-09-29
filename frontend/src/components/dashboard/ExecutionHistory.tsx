"use client";
import { useState } from "react";
import { Eye, History } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { Run } from "@/lib/types";
import { formatDuration } from "@/lib/time";
import { BriefingContent } from "./BriefingCard";
import { EmptyState, ErrorState, LoadingState } from "./states";
import { StatusBadge } from "./StatusBadge";

export function ExecutionHistory({ runs, loading, error, onRetry, timezone }: { runs?: Run[]; loading?: boolean; error?: string; onRetry?: () => void; timezone: string }) {
  const [open, setOpen] = useState<Run | null>(null);
  const fmt = (iso: string) => new Intl.DateTimeFormat("en-IN", { timeZone: timezone, day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: true }).format(new Date(iso));
  return (
    <Card id="history" aria-label="Execution history">
      <CardHeader><CardTitle className="flex items-center gap-2 text-base"><History className="size-4 text-primary" aria-hidden />Execution history</CardTitle></CardHeader>
      <CardContent>
        {loading ? <LoadingState lines={4} label="Loading history" />
          : error ? <ErrorState message={error} onRetry={onRetry} />
          : !runs?.length ? <EmptyState title="No runs yet" description="Runs appear here after the schedule fires or you generate a briefing manually." />
          : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[520px] text-left text-sm">
                <caption className="sr-only">Previous briefing runs</caption>
                <thead className="text-xs text-muted-foreground"><tr><th scope="col" className="pb-2 font-medium">Time</th><th scope="col" className="pb-2 font-medium">Trigger</th><th scope="col" className="pb-2 font-medium">Status</th><th scope="col" className="pb-2 font-medium">Duration</th><th scope="col" className="pb-2 text-right font-medium">Briefing</th></tr></thead>
                <tbody className="divide-y">
                  {runs.map((r) => (
                    <tr key={r.id} className="animate-in fade-in">
                      <td className="py-2.5 tabular-nums">{fmt(r.startedAt)}</td>
                      <td className="py-2.5 capitalize">{r.trigger}</td>
                      <td className="py-2.5"><StatusBadge status={r.status} /></td>
                      <td className="py-2.5 tabular-nums">{formatDuration(r.durationMs)}</td>
                      <td className="py-2.5 text-right">
                        {r.briefing ? <Button variant="white" size="xs" onClick={() => setOpen(r)} aria-label={`View briefing from ${fmt(r.startedAt)}`}><Eye />View</Button>
                          : <span className="text-xs text-muted-foreground" title={r.error}>No briefing</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </CardContent>
      <Dialog open={!!open} onOpenChange={(o) => !o && setOpen(null)}>
        <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-xl">
          <DialogHeader><DialogTitle>{open?.briefing?.subject}</DialogTitle><DialogDescription>{open && `${fmt(open.startedAt)} · ${open.status === "partial" ? "delivered with warnings" : open.status}`}</DialogDescription></DialogHeader>
          {open?.briefing && <BriefingContent briefing={open.briefing} />}
        </DialogContent>
      </Dialog>
    </Card>
  );
}
