import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** Maps a 0-100 score to a semantic tone used across the UI. */
export function scoreTone(score: number): "good" | "medium" | "poor" {
  if (score >= 75) return "good";
  if (score >= 50) return "medium";
  return "poor";
}

export const scoreToneClasses: Record<ReturnType<typeof scoreTone>, string> = {
  good: "text-emerald-600 bg-emerald-50 border-emerald-200",
  medium: "text-amber-600 bg-amber-50 border-amber-200",
  poor: "text-rose-600 bg-rose-50 border-rose-200",
};

export function titleCase(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
