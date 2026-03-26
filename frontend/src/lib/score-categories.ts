/**
 * Score → category mapping that mirrors the backend
 * `job_application_analysis.score_categories` module.
 *
 * Backend serializers include `score_category` on every analysis object,
 * but this client-side helper is kept for situations where only the raw
 * score is available (e.g. computing styles before the full payload).
 */

export type ScoreCategory = {
  key: "suitable" | "potentially_suitable" | "unsuitable";
  label: string;
};

const THRESHOLDS: { min: number; category: ScoreCategory }[] = [
  { min: 70, category: { key: "suitable", label: "Suitable" } },
  { min: 40, category: { key: "potentially_suitable", label: "Potentially Suitable" } },
  { min: 0, category: { key: "unsuitable", label: "Unsuitable" } },
];

export function getScoreCategory(
  score: number | null | undefined,
): ScoreCategory | null {
  if (score == null) return null;
  for (const t of THRESHOLDS) {
    if (score >= t.min) return t.category;
  }
  return { key: "unsuitable", label: "Unsuitable" };
}

/** Tailwind colour classes keyed by category. */
export const SCORE_CATEGORY_COLORS: Record<
  ScoreCategory["key"],
  { text: string; border: string; bg: string }
> = {
  suitable: {
    text: "text-emerald-600",
    border: "border-emerald-500",
    bg: "bg-emerald-100",
  },
  potentially_suitable: {
    text: "text-amber-600",
    border: "border-amber-400",
    bg: "bg-amber-100",
  },
  unsuitable: {
    text: "text-destructive",
    border: "border-red-400",
    bg: "bg-red-100",
  },
};
