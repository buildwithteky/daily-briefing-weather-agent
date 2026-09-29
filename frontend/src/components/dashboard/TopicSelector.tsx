"use client";
import { Calendar, Check, Cloud, ListChecks, Newspaper, Sun, Wallet } from "lucide-react";
import type { TopicId } from "@/lib/types";

export const TOPICS: { id: TopicId; label: string; icon: typeof Sun }[] = [
  { id: "weather", label: "Weather", icon: Sun },
  { id: "aws", label: "AWS & Cloud", icon: Cloud },
  { id: "tech", label: "Tech news", icon: Newspaper },
  { id: "calendar", label: "Calendar", icon: Calendar },
  { id: "tasks", label: "Tasks from email", icon: ListChecks },
  { id: "billing", label: "AWS billing", icon: Wallet },
];

export function TopicSelector({ value, onChange, disabled }: { value: TopicId[]; onChange: (v: TopicId[]) => void; disabled?: boolean }) {
  const toggle = (id: TopicId) => onChange(value.includes(id) ? value.filter((t) => t !== id) : [...value, id]);
  return (
    <div role="group" aria-label="Briefing topics" className="flex flex-wrap gap-2">
      {TOPICS.map(({ id, label, icon: Icon }) => {
        const on = value.includes(id);
        return (
          <button key={id} type="button" aria-pressed={on} disabled={disabled} onClick={() => toggle(id)}
            className={`inline-flex h-9 items-center gap-1.5 rounded-[4px] border px-3 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 ${on ? "border-[#262525] bg-[#262525] text-white" : "bg-white hover:bg-muted"}`}>
            {on ? <Check className="size-4" aria-hidden /> : <Icon className="size-4" aria-hidden />}{label}
          </button>
        );
      })}
    </div>
  );
}
