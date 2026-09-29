import { Bot, CalendarClock, CheckCircle2, CloudSun, Loader2, Send, User, XCircle, Zap, ChevronRight } from "lucide-react";
import type { StepId, StepState } from "@/lib/types";

export const STEPS: { id: StepId; label: string; sub: string; icon: typeof Bot }[] = [
  { id: "scheduler", label: "EventBridge", sub: "Scheduler", icon: CalendarClock },
  { id: "lambda", label: "Lambda", sub: "Runs code", icon: Zap },
  { id: "weather", label: "Weather API", sub: "Fetch data", icon: CloudSun },
  { id: "bedrock", label: "Bedrock", sub: "AI summary", icon: Bot },
  { id: "sns", label: "SNS", sub: "Sends email", icon: Send },
  { id: "user", label: "You", sub: "Inbox", icon: User },
];

export function WorkflowStatus({ states }: { states: Record<StepId, StepState> }) {
  return (
    <nav aria-label="Backend workflow" className="rounded-[4px] border bg-card p-3">
      <ol className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-0">
        {STEPS.map((s, i) => {
          const st = states[s.id];
          const Icon = s.icon;
          const ring = st === "done" ? "border-success bg-success/10 text-success" : st === "running" ? "border-primary bg-primary/10 text-primary animate-pulse" : st === "failed" ? "border-destructive bg-destructive/10 text-destructive" : "border-border bg-muted text-muted-foreground";
          return (
            <li key={s.id} className="flex flex-1 items-center gap-2 sm:justify-center" aria-label={`${s.label}: ${st}`}>
              <span className={`relative flex size-9 shrink-0 items-center justify-center rounded-[4px] border transition-colors duration-300 ${ring}`}>
                {st === "running" ? <Loader2 className="size-4 animate-spin" aria-hidden /> : st === "done" ? <CheckCircle2 className="size-4" aria-hidden /> : st === "failed" ? <XCircle className="size-4" aria-hidden /> : <Icon className="size-4" aria-hidden />}
              </span>
              <span className="min-w-0 leading-tight"><span className="block text-sm font-medium">{s.label}</span><span className="block text-xs text-muted-foreground">{s.sub}</span></span>
              {i < STEPS.length - 1 && <ChevronRight className="ml-auto hidden size-4 shrink-0 text-muted-foreground sm:block" aria-hidden />}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
