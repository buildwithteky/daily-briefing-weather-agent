import { Cloud, CloudRain, CloudSun, Droplets, MapPin, Sun, Wind, Zap } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Weather } from "@/lib/types";
import { ErrorState, LoadingState } from "./states";

const ICONS = { clear: Sun, cloudy: Cloud, rain: CloudRain, storm: Zap, partly: CloudSun };

interface Props { weather?: Weather; loading?: boolean; error?: string; onRetry?: () => void }

export function WeatherCard({ weather, loading, error, onRetry }: Props) {
  return (
    <Card className="overflow-hidden border-0 bg-[#262525] text-white" aria-label="Current weather">
      <CardContent className="p-5 sm:p-6">
        {loading ? (
          <div className="[&_*]:bg-white/15"><LoadingState lines={2} label="Loading weather" /></div>
        ) : error ? (
          <div className="bg-white rounded-[4px]"><ErrorState title="Weather unavailable" message={error} onRetry={onRetry} /></div>
        ) : weather ? (
          <div className="flex flex-wrap items-center justify-between gap-6 animate-in fade-in duration-500">
            <div>
              <p className="flex items-center gap-1.5 text-sm text-white/70"><MapPin className="size-4" aria-hidden />{weather.city}, {weather.country}</p>
              <p className="mt-2 text-6xl font-medium leading-none tabular-nums sm:text-7xl">{Math.round(weather.temperature)}°<span className="text-3xl text-white/60">C</span></p>
              <p className="mt-2 text-lg">{weather.conditionLabel} <span className="text-sm text-white/60">· feels like {Math.round(weather.feelsLike)}°</span></p>
            </div>
            <div className="flex flex-col items-end gap-4">
              {(() => { const Icon = ICONS[weather.condition]; return <Icon className="size-16 text-[#F9632D]" aria-hidden />; })()}
              {weather.status !== "ok" && <Badge className="rounded-[4px] bg-amber-500/20 text-amber-200">Data may be out of date</Badge>}
            </div>
            <dl className="grid w-full grid-cols-2 gap-3 border-t border-white/15 pt-4 text-sm sm:grid-cols-4">
              <Stat icon={Droplets} label="Humidity" value={`${weather.humidity}%`} />
              <Stat icon={Wind} label="Wind" value={`${weather.windKmh} km/h`} />
              <Stat icon={Sun} label="High / Low" value={`${weather.high}° / ${weather.low}°`} />
              <Stat icon={CloudRain} label="Rain chance" value={`${weather.rainChance}%`} />
            </dl>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function Stat({ icon: Icon, label, value }: { icon: typeof Sun; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="size-4 text-white/60" aria-hidden />
      <div><dt className="text-xs text-white/60">{label}</dt><dd className="font-medium">{value}</dd></div>
    </div>
  );
}
