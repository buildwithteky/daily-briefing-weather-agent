"use client";
import { useEffect, useId, useState } from "react";
import { Loader2, MapPin, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import type { Location } from "@/lib/types";
import { searchCities } from "@/services/briefingApi";

const label = (l: Location) => [l.name, l.admin1, l.country].filter(Boolean).join(", ");

/** Accessible combobox (ARIA 1.2 pattern): type to search, arrows to move, Enter to pick, Esc to close. */
export function CitySearch({ value, onSelect, invalid }: { value: Location; onSelect: (l: Location) => void; invalid?: boolean }) {
  const id = useId();
  const [text, setText] = useState(label(value));
  const [results, setResults] = useState<Location[]>([]);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [active, setActive] = useState(0);
  const [typed, setTyped] = useState(false); // only search after the user types, not on first render

  useEffect(() => {
    if (!typed) return;
    const q = text.trim();
    const ctrl = new AbortController();
    const timer = setTimeout(async () => {
      if (q.length < 2) { setResults([]); setBusy(false); return; }
      setBusy(true); setError(undefined);
      try { setResults(await searchCities(q, ctrl.signal)); setActive(0); }
      catch (e) { if ((e as Error).name !== "AbortError") setError((e as Error).message); }
      setBusy(false);
    }, 300); // debounce
    return () => { clearTimeout(timer); ctrl.abort(); };
  }, [text, typed]);

  const pick = (l: Location) => { onSelect(l); setText(label(l)); setOpen(false); setTyped(false); };
  const q = text.trim();
  const showList = open && typed && q.length >= 2;

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setOpen(true); setActive((a) => Math.min(a + 1, results.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
    else if (e.key === "Enter" && showList && results[active]) { e.preventDefault(); pick(results[active]); }
    else if (e.key === "Escape") setOpen(false);
  };

  return (
    <div className="relative">
      <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
      <Input id="city" role="combobox" aria-expanded={showList} aria-controls={`${id}-list`} aria-autocomplete="list"
        aria-activedescendant={showList && results[active] ? `${id}-opt-${active}` : undefined} aria-invalid={invalid}
        autoComplete="off" className="pl-8 pr-8" placeholder="Search a city…" value={text}
        onChange={(e) => { setTyped(true); setText(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)} onBlur={() => setTimeout(() => { setOpen(false); if (typed) { setText(label(value)); setTyped(false); } }, 150)}
        onKeyDown={onKey} />
      {busy && <Loader2 className="absolute right-2.5 top-1/2 size-4 -translate-y-1/2 animate-spin text-muted-foreground" aria-hidden />}
      {showList && (
        <ul id={`${id}-list`} role="listbox" aria-label="City suggestions" className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-[4px] border bg-popover p-1 shadow-lg">
          {error ? <li role="alert" className="p-2 text-sm text-destructive">{error}</li>
            : busy && !results.length ? <li className="p-2 text-sm text-muted-foreground">Searching…</li>
            : !results.length ? <li className="p-2 text-sm text-muted-foreground">No cities found for “{q}”.</li>
            : results.map((r, i) => (
              <li key={`${r.latitude},${r.longitude}`} id={`${id}-opt-${i}`} role="option" aria-selected={i === active}
                onMouseDown={(e) => { e.preventDefault(); pick(r); }} onMouseEnter={() => setActive(i)}
                className={`flex cursor-pointer items-center gap-2 rounded-[4px] px-2 py-1.5 text-sm ${i === active ? "bg-muted" : ""}`}>
                <MapPin className="size-4 shrink-0 text-primary" aria-hidden />
                <span className="min-w-0 truncate"><span className="font-medium">{r.name}</span><span className="text-muted-foreground">{[r.admin1, r.country].filter(Boolean).length ? ", " + [r.admin1, r.country].filter(Boolean).join(", ") : ""}</span></span>
                <span className="ml-auto shrink-0 text-xs text-muted-foreground">{r.timezone}</span>
              </li>))}
        </ul>
      )}
    </div>
  );
}
