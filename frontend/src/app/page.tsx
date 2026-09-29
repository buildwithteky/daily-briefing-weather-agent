"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Newspaper, Play } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import * as api from "@/services/briefingApi";
import type { Briefing, Location, Run, ServiceHealth, Settings, StepId, StepState, Weather } from "@/lib/types";
import { formatDateTime, nextRunAt } from "@/lib/time";
import { WeatherCard } from "@/components/dashboard/WeatherCard";
import { BriefingCard } from "@/components/dashboard/BriefingCard";
import { ScheduleCard } from "@/components/dashboard/ScheduleCard";
import { WorkflowStatus } from "@/components/dashboard/WorkflowStatus";
import { NotificationStatus } from "@/components/dashboard/NotificationStatus";
import { ExecutionHistory } from "@/components/dashboard/ExecutionHistory";
import { SettingsPanel } from "@/components/dashboard/SettingsPanel";
import { SystemHealth } from "@/components/dashboard/SystemHealth";

const IDLE: Record<StepId, StepState> = { scheduler: "idle", lambda: "idle", weather: "idle", bedrock: "idle", sns: "idle", user: "idle" };
const RUNNING: Record<StepId, StepState> = { ...IDLE, lambda: "running" };
const msg = (e: unknown) => (e instanceof Error ? e.message : "Unexpected error");

export default function Dashboard() {
  const [settings, setSettings] = useState<Settings>();
  const [settingsErr, setSettingsErr] = useState<string>();
  const [weather, setWeather] = useState<Weather>();
  const [weatherErr, setWeatherErr] = useState<string>();
  const [briefing, setBriefing] = useState<Briefing | null>();
  const [briefingErr, setBriefingErr] = useState<string>();
  const [runs, setRuns] = useState<Run[]>();
  const [runsErr, setRunsErr] = useState<string>();
  const [health, setHealth] = useState<ServiceHealth[]>();
  const [healthErr, setHealthErr] = useState<string>();
  const [healthLoading, setHealthLoading] = useState(false);

  const [saving, setSaving] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [generating, setGenerating] = useState(false);

  const loadWeather = useCallback((loc: Location) => {
    api.getWeather(loc).then((w) => { setWeather(w); setWeatherErr(undefined); }).catch((e) => setWeatherErr(msg(e)));
  }, []);
  const loadBriefing = useCallback(() => {
    api.getLatestBriefing().then((b) => { setBriefing(b); setBriefingErr(undefined); }).catch((e) => setBriefingErr(msg(e)));
  }, []);
  const loadRuns = useCallback(() => {
    api.getHistory().then((r) => { setRuns(r); setRunsErr(undefined); }).catch((e) => setRunsErr(msg(e)));
  }, []);
  const loadHealth = useCallback(() => {
    api.getSystemHealth()
      .then((h) => { setHealth(h); setHealthErr(undefined); })
      .catch((e) => setHealthErr(msg(e)))
      .finally(() => setHealthLoading(false));
  }, []);
  const loadSettings = useCallback(() => {
    api.getSettings()
      .then((s) => { setSettings(s); setSettingsErr(undefined); loadWeather(s.location); })
      .catch((e) => setSettingsErr(msg(e)));
  }, [loadWeather]);

  const retryWeather = (loc: Location) => { setWeather(undefined); setWeatherErr(undefined); loadWeather(loc); };
  const retryBriefing = () => { setBriefing(undefined); setBriefingErr(undefined); loadBriefing(); };
  const retryRuns = () => { setRuns(undefined); setRunsErr(undefined); loadRuns(); };
  const refreshHealth = () => { setHealthLoading(true); loadHealth(); };
  const retrySettings = () => { setSettings(undefined); setSettingsErr(undefined); loadSettings(); };

  useEffect(() => { loadSettings(); loadBriefing(); loadRuns(); loadHealth(); }, [loadSettings, loadBriefing, loadRuns, loadHealth]);

  const save = async (next: Settings) => {
    setSaving(true);
    try {
      const prev = settings;
      const saved = await api.saveSettings(next);
      setSettings(saved);
      toast.success("Settings saved", { description: `Next briefing at ${saved.time} ${saved.timezone}.` });
      if (saved.location.latitude !== prev?.location.latitude || saved.location.longitude !== prev?.location.longitude) retryWeather(saved.location);
      if (saved.email !== prev?.email) toast.warning("Confirm your email", { description: "AWS sent a subscription confirmation to " + saved.email });
      refreshHealth();
    } catch (e) { toast.error("Could not save settings", { description: msg(e) }); }
    setSaving(false);
  };

  const toggle = async (enabled: boolean) => {
    setToggling(true);
    try {
      setSettings(await api.setScheduleEnabled(enabled));
      toast.success(enabled ? "Daily briefing enabled" : "Daily briefing paused");
      refreshHealth();
    } catch (e) { toast.error("Could not change schedule", { description: msg(e) }); }
    setToggling(false);
  };

  const generate = async () => {
    setGenerating(true);
    const t = toast.loading("Running the Lambda…");
    try {
      const run = await api.generateBriefing(() => undefined);
      setRuns((r) => [run, ...(r ?? []).filter((x) => x.id !== run.id)]);
      setBriefing(run.briefing ?? null);
      if (run.status === "partial") toast.warning("Briefing sent with warnings", { id: t, description: run.error });
      else if (run.status === "generated") toast.info("Briefing generated but not emailed", { id: t, description: "Email is switched off in Settings." });
      else toast.success("Briefing delivered", { id: t, description: `Sent to ${run.recipient}` });
    } catch (e) {
      const run = (e as { run?: Run }).run;
      if (run) setRuns((r) => [run, ...(r ?? []).filter((x) => x.id !== run.id)]);
      toast.error("Briefing failed", { id: t, description: msg(e) });
    }
    refreshHealth();
    setGenerating(false);
  };

  const latest = runs?.[0];
  const steps = generating ? RUNNING : latest ? api.stepsFromRun(latest) : IDLE;
  const nextLabel = useMemo(() => settings?.enabled ? formatDateTime(nextRunAt(settings.time, settings.timezone), settings.timezone) : undefined, [settings]);

  return (
    <div className="min-h-screen">
      <header className="border-b bg-card">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2.5">
            <span className="flex size-9 items-center justify-center rounded-[4px] bg-[#F9632D] text-white"><Newspaper className="size-5" aria-hidden /></span>
            <div className="leading-tight"><h1 className="text-lg font-semibold">Daily Briefing Agent</h1><p className="text-xs text-muted-foreground">Runs on AWS. No clicks needed.</p></div>
          </div>
          <nav aria-label="Sections" className="hidden gap-4 text-sm sm:flex">
            <a className="hover:underline focus-visible:outline-2 focus-visible:outline-ring" href="#history">History</a>
            <a className="hover:underline focus-visible:outline-2 focus-visible:outline-ring" href="#settings">Settings</a>
          </nav>
          <Button onClick={generate} disabled={generating} aria-busy={generating}><Play />{generating ? "Generating…" : "Generate briefing now"}</Button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-5 px-4 py-5 sm:px-6">
        <WorkflowStatus states={steps} />

        <div className="grid gap-5 lg:grid-cols-3">
          <div className="space-y-5 lg:col-span-2">
            <WeatherCard weather={weather} loading={!weather && !weatherErr} error={weatherErr} onRetry={() => settings && retryWeather(settings.location)} />
            <BriefingCard briefing={briefing} loading={briefing === undefined && !briefingErr} generating={generating} error={briefingErr} onRetry={retryBriefing} onGenerate={generate} />
          </div>
          <div className="space-y-5">
            <ScheduleCard settings={settings} loading={!settings && !settingsErr} toggling={toggling} onToggle={toggle} />
            <NotificationStatus run={latest} loading={!runs && !runsErr} generating={generating} error={runsErr} onRetry={retryRuns} nextLabel={nextLabel} />
            <SystemHealth services={health} loading={healthLoading || (!health && !healthErr)} error={healthErr} onRefresh={refreshHealth} />
          </div>
        </div>

        <ExecutionHistory runs={runs} loading={!runs && !runsErr} error={runsErr} onRetry={retryRuns} timezone={settings?.timezone ?? "Asia/Kolkata"} />
        <SettingsPanel settings={settings} loading={!settings && !settingsErr} saving={saving} error={settingsErr} onSave={save} onRetry={retrySettings} />
      </main>

      <footer className="mx-auto max-w-6xl px-4 py-6 text-xs text-muted-foreground sm:px-6">
        All data is live from your AWS account through this app&apos;s server routes. No AWS credentials are used in the browser.
      </footer>
    </div>
  );
}
