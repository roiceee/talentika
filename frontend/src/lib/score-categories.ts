/**
 * Score category helpers that mirror the backend
 * `job_application_analysis.score_categories` module.
 *
 * The AI returns a category key directly — there is no intermediate numeric
 * score.  The backend serializer always includes `score_category` as a
 * `{key, label}` object on every completed analysis.
 */

export type ScoreCategory = {
  key: "suitable" | "potentially_suitable" | "unsuitable";
  label: string;
};

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
