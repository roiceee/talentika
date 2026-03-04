import type { JobProfileFormValues } from "./types";

export const DEFAULT_VALUES: JobProfileFormValues = {
  title: "",
  category: "",
  employment_type: "full_time",
  experience_level: "",
  description: "",
  qualifications: [],
  questions: [],
  is_active: true,
};

export const EMPLOYMENT_TYPE_OPTIONS = [
  { value: "full_time", label: "Full Time" },
  { value: "part_time", label: "Part Time" },
  { value: "contract", label: "Contract" },
  { value: "internship", label: "Internship" },
  { value: "freelance", label: "Freelance" },
  { value: "not_applicable", label: "Not Applicable" },
] as const;

export const QUESTION_TYPE_OPTIONS = [
  { value: "text", label: "Text (free-form)" },
  { value: "mcq", label: "Multiple Choice (multi-select)" },
  { value: "mcq_single", label: "Multiple Choice (single select)" },
] as const;

export const QUALIFICATION_CATEGORY_OPTIONS = [
  { value: "skill", label: "Skill" },
  { value: "experience", label: "Experience" },
  { value: "education", label: "Education" },
  { value: "certification", label: "Certification" },
  { value: "tool", label: "Tool" },
  { value: "language", label: "Language" },
  { value: "other", label: "Other" },
] as const;

export const PROFICIENCY_LEVEL_OPTIONS = [
  { value: "none", label: "Not specified" },
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
  { value: "expert", label: "Expert" },
] as const;
