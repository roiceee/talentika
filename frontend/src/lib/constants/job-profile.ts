/**
 * Shared constants for job profile display across the app.
 * Centralised here to avoid duplication in pages and components.
 */

export const EMPLOYMENT_TYPE_LABELS: Record<string, string> = {
  full_time: "Full Time",
  part_time: "Part Time",
  contract: "Contract",
  internship: "Internship",
  freelance: "Freelance",
  not_applicable: "Not Applicable",
};

export const QUESTION_TYPE_LABELS: Record<string, string> = {
  text: "Text",
  mcq: "Multiple Choice (multi)",
  mcq_single: "Multiple Choice (single)",
};

export const QUALIFICATION_CATEGORY_LABELS: Record<string, string> = {
  skill: "Skills",
  experience: "Experience",
  education: "Education",
  certification: "Certifications",
  tool: "Tools",
  language: "Languages",
  other: "Other",
};

export const QUALIFICATION_CATEGORY_COLORS: Record<string, string> = {
  skill: "bg-blue-100 text-blue-800",
  experience: "bg-amber-100 text-amber-800",
  education: "bg-purple-100 text-purple-800",
  certification: "bg-green-100 text-green-800",
  tool: "bg-slate-100 text-slate-800",
  language: "bg-pink-100 text-pink-800",
  other: "bg-gray-100 text-gray-800",
};
