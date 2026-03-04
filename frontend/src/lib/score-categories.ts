/**
 * Score → category mapping that mirrors the backend
 * `job_application_analysis.score_categories` module.
 *
 * Backend serializers include `score_category` on every analysis object,
 * but this client-side helper is kept for situations where only the raw
 * score is available (e.g. computing styles before the full payload).
 */

export type ScoreCategory = {
  key: "excellent" | "good" | "moderate" | "bad";
  label: string;
};

const THRESHOLDS: { min: number; category: ScoreCategory }[] = [
  { min: 90, category: { key: "excellent", label: "Excellent" } },
  { min: 75, category: { key: "good", label: "Good" } },
  { min: 40, category: { key: "moderate", label: "Moderate" } },
  { min: 0, category: { key: "bad", label: "Bad" } },
];

export function getScoreCategory(
  score: number | null | undefined,
): ScoreCategory | null {
  if (score == null) return null;
  for (const t of THRESHOLDS) {
    if (score >= t.min) return t.category;
  }
  return { key: "bad", label: "Bad" };
}

/** Tailwind colour classes keyed by category. */
export const SCORE_CATEGORY_COLORS: Record<
  ScoreCategory["key"],
  { text: string; border: string; bg: string }
> = {
  excellent: {
    text: "text-emerald-600",
    border: "border-emerald-500",
    bg: "bg-emerald-100",
  },
  good: {
    text: "text-blue-600",
    border: "border-blue-400",
    bg: "bg-blue-100",
  },
  moderate: {
    text: "text-amber-600",
    border: "border-amber-400",
    bg: "bg-amber-100",
  },
  bad: {
    text: "text-destructive",
    border: "border-red-400",
    bg: "bg-red-100",
  },
};
