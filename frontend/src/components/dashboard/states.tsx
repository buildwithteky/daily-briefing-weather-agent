import { AlertTriangle, Inbox, RefreshCw, type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

/** Skeleton placeholder. `lines` controls how many text rows are shown. */
export function LoadingState({ lines = 3, label = "Loading" }: { lines?: number; label?: string }) {
  return (
    <div role="status" aria-live="polite" aria-busy="true" className="space-y-3">
      <span className="sr-only">{label}…</span>
      <Skeleton className="h-8 w-1/3" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-4" style={{ width: `${90 - i * 12}%` }} />
      ))}
    </div>
  );
}

export function ErrorState({ title = "Something went wrong", message, onRetry }: { title?: string; message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-start gap-3 rounded-[4px] border border-destructive/30 bg-destructive/5 p-4">
      <div className="flex items-center gap-2 font-medium text-destructive"><AlertTriangle className="size-4" aria-hidden />{title}</div>
      <p className="text-sm text-muted-foreground">{message}</p>
      {onRetry && <Button variant="white" size="sm" onClick={onRetry}><RefreshCw />Try again</Button>}
    </div>
  );
}

export function EmptyState({ icon: Icon = Inbox, title, description, action }: { icon?: LucideIcon; title: string; description: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-[4px] border border-dashed p-8 text-center">
      <Icon className="size-8 text-muted-foreground" aria-hidden />
      <p className="font-medium">{title}</p>
      <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      {action}
    </div>
  );
}
