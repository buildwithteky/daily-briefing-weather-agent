import { Bot, Cloud, ListChecks, Newspaper, Sun, TriangleAlert } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Briefing } from "@/lib/types";
import { EmptyState, ErrorState, LoadingState } from "./states";

const ICON = { weather: Sun, aws: Cloud, tech: Newspaper, tasks: ListChecks, summary: Bot };

interface Props { briefing?: Briefing | null; loading?: boolean; generating?: boolean; error?: string; onRetry?: () => void; onGenerate?: () => void; title?: string; bare?: boolean }

export function BriefingContent({ briefing }: { briefing: Briefing }) {
  return (
    <div className="space-y-5 animate-in fade-in duration-500">
      {briefing.sections.map((s) => {
        const Icon = ICON[s.id];
        return (
          <section key={s.id} aria-labelledby={`sec-${briefing.id}-${s.id}`} className={s.id === "summary" ? "rounded-[4px] border-l-4 border-primary bg-primary/5 p-4" : ""}>
            <h3 id={`sec-${briefing.id}-${s.id}`} className="mb-2 flex items-center gap-2 text-sm font-semibold">
              <Icon className="size-4 text-primary" aria-hidden />{s.title}
              {s.status === "unavailable" && <Badge className="rounded-[4px] bg-amber-100 text-amber-800"><TriangleAlert className="size-3" aria-hidden />Unavailable</Badge>}
              {s.status === "stale" && <Badge className="rounded-[4px] bg-amber-100 text-amber-800">May be stale</Badge>}
            </h3>
            {s.id === "summary" || s.status === "unavailable" ? (
              <p className={`whitespace-pre-line text-sm leading-relaxed ${s.status === "unavailable" ? "text-muted-foreground italic" : ""}`}>{s.items[0]}</p>
            ) : (
              <ul className="list-disc space-y-1 pl-5 text-sm leading-relaxed marker:text-primary">{s.items.map((it) => <li key={it}>{it}</li>)}</ul>
            )}
          </section>
        );
      })}
    </div>
  );
}

export function BriefingCard({ briefing, loading, generating, error, onRetry, onGenerate }: Props) {
  return (
    <Card aria-label="Briefing preview" aria-busy={loading || generating}>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Briefing preview</CardTitle>
        {briefing && <span className="text-xs text-muted-foreground">{new Date(briefing.generatedAt).toLocaleString("en-IN")}</span>}
      </CardHeader>
      <CardContent>
        {loading || generating ? <LoadingState lines={6} label={generating ? "Generating briefing" : "Loading briefing"} />
          : error ? <ErrorState title="Could not load briefing" message={error} onRetry={onRetry} />
          : !briefing ? <EmptyState icon={Bot} title="No briefing yet" description="Generate your first briefing to see what will land in your inbox." action={onGenerate && <button onClick={onGenerate} className="text-sm font-medium text-primary underline">Generate now</button>} />
          : <BriefingContent briefing={briefing} />}
      </CardContent>
    </Card>
  );
}
