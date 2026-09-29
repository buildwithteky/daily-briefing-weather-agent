"use client";
import { useState } from "react";
import { Save, Settings as SettingsIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Settings } from "@/lib/types";
import { TIMEZONES } from "@/lib/time";
import { ErrorState, LoadingState } from "./states";
import { CitySearch } from "./CitySearch";
import { TopicSelector } from "./TopicSelector";

type Errors = Partial<Record<"name" | "city" | "email" | "topics" | "time", string>>;

function validate(s: Settings): Errors {
  const e: Errors = {};
  if (!s.city.trim()) e.city = "Enter a city.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s.email)) e.email = "Enter a valid email address.";
  if (!s.topics.length) e.topics = "Pick at least one topic.";
  if (!/^\d{2}:\d{2}$/.test(s.time)) e.time = "Choose a delivery time.";
  return e;
}

export function SettingsPanel({ settings, loading, saving, error, onSave, onRetry }: { settings?: Settings; loading?: boolean; saving?: boolean; error?: string; onSave: (s: Settings) => void; onRetry?: () => void }) {
  const [draft, setDraft] = useState<Settings | undefined>(settings);
  const [errors, setErrors] = useState<Errors>({});
  const [prev, setPrev] = useState(settings);
  if (prev !== settings) { setPrev(settings); setDraft(settings); } // reset form when saved settings change
  const set = <K extends keyof Settings>(k: K, v: Settings[K]) => draft && setDraft({ ...draft, [k]: v });
  const dirty = JSON.stringify(draft) !== JSON.stringify(settings);

  const submit = (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!draft) return;
    const e = validate(draft);
    setErrors(e);
    if (!Object.keys(e).length) onSave(draft);
  };

  return (
    <Card id="settings" aria-label="Settings">
      <CardHeader><CardTitle className="flex items-center gap-2 text-base"><SettingsIcon className="size-4 text-primary" aria-hidden />Settings</CardTitle></CardHeader>
      <CardContent>
        {loading ? <LoadingState lines={5} label="Loading settings" />
          : error ? <ErrorState message={error} onRetry={onRetry} />
          : draft && (
            <form onSubmit={submit} noValidate className="grid gap-5 md:grid-cols-2">
              <Field id="name" label="Your name (used in the greeting)" error={errors.name}>
                <Input id="name" value={draft.userName} maxLength={40} onChange={(e) => set("userName", e.target.value)} placeholder="Optional" />
              </Field>
              <Field id="city" label="City" error={errors.city}>
                <CitySearch value={draft.location} invalid={!!errors.city}
                  onSelect={(l) => setDraft({ ...draft, city: l.name, location: l, timezone: l.timezone })} />
                <p className="text-xs text-muted-foreground">Type at least 2 letters, then pick a city. Timezone updates automatically.</p>
              </Field>
              <Field id="tz" label="Timezone">
                <Select value={draft.timezone} onValueChange={(v) => v && set("timezone", v)}>
                  <SelectTrigger id="tz" className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>{(TIMEZONES.includes(draft.timezone) ? TIMEZONES : [draft.timezone, ...TIMEZONES]).map((z) => <SelectItem key={z} value={z}>{z}</SelectItem>)}</SelectContent>
                </Select>
              </Field>
              <Field id="time" label="Delivery time" error={errors.time}>
                <Input id="time" type="time" value={draft.time} onChange={(e) => set("time", e.target.value)} aria-invalid={!!errors.time} />
              </Field>
              <Field id="email" label="Notification email" error={errors.email}>
                <Input id="email" type="email" value={draft.email} onChange={(e) => set("email", e.target.value)} aria-invalid={!!errors.email} aria-describedby={errors.email ? "email-err" : "email-hint"} placeholder="you@example.com" />
                <p id="email-hint" className="text-xs text-muted-foreground">AWS will ask this address to confirm the subscription.</p>
              </Field>
              <div className="space-y-2 md:col-span-2">
                <Label>Briefing topics</Label>
                <TopicSelector value={draft.topics} onChange={(v) => set("topics", v)} />
                {errors.topics && <p role="alert" className="text-xs text-destructive">{errors.topics}</p>}
              </div>
              <fieldset className="space-y-2 md:col-span-2">
                <legend className="mb-2 text-sm font-medium">Notification preferences</legend>
                <label className="flex items-center gap-2 text-sm"><Checkbox checked={draft.notifyOnSuccess} onCheckedChange={(c) => set("notifyOnSuccess", !!c)} />Email me the briefing every day</label>
                <label className="flex items-center gap-2 text-sm"><Checkbox checked={draft.notifyOnFailure} onCheckedChange={(c) => set("notifyOnFailure", !!c)} />Email me if a run fails</label>
              </fieldset>
              <div className="flex items-center gap-3 md:col-span-2">
                <Button type="submit" disabled={saving || !dirty}><Save />{saving ? "Saving…" : "Save settings"}</Button>
                {dirty && !saving && <span className="text-xs text-muted-foreground">Unsaved changes</span>}
              </div>
            </form>
          )}
      </CardContent>
    </Card>
  );
}

function Field({ id, label, error, children }: { id: string; label: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error && <p id={`${id}-err`} role="alert" className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
