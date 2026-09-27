import { cn, scoreTone } from "@/lib/utils";

const toneBar: Record<ReturnType<typeof scoreTone>, string> = {
  good: "bg-emerald-500",
  medium: "bg-amber-500",
  poor: "bg-rose-500",
};

export function Progress({
  value,
  className,
  colorByScore = false,
}: {
  value: number;
  className?: string;
  colorByScore?: boolean;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div
      role="progressbar"
      aria-valuenow={Math.round(clamped)}
      aria-valuemin={0}
      aria-valuemax={100}
      className={cn("h-2 w-full overflow-hidden rounded-full bg-slate-100", className)}
    >
      <div
        className={cn(
          "h-full rounded-full transition-all",
          colorByScore ? toneBar[scoreTone(clamped)] : "bg-brand-500",
        )}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
