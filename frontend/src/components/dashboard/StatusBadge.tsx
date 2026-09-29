import { AlertTriangle, CheckCircle2, CalendarClock, Loader2, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { RunStatus } from "@/lib/types";

const MAP = {
  delivered: { label: "Delivered", cls: "border-success/30 bg-success/10 text-success", Icon: CheckCircle2 },
  partial: { label: "Delivered with warnings", cls: "border-warning/30 bg-warning/10 text-warning", Icon: AlertTriangle },
  generated: { label: "Generated, not emailed", cls: "border-border bg-muted text-foreground", Icon: CheckCircle2 },
  failed: { label: "Failed", cls: "border-destructive/30 bg-destructive/10 text-destructive", Icon: XCircle },
  generating: { label: "Generating", cls: "border-primary/30 bg-primary/10 text-[#b8400f]", Icon: Loader2 },
  scheduled: { label: "Scheduled", cls: "border-border bg-muted text-foreground", Icon: CalendarClock },
} as const;

export function StatusBadge({ status }: { status: RunStatus }) {
  const { label, cls, Icon } = MAP[status];
  return (
    <Badge variant="outline" className={`gap-1 rounded-[4px] ${cls}`}>
      <Icon className={`size-3 ${status === "generating" ? "animate-spin" : ""}`} aria-hidden />{label}
    </Badge>
  );
}
