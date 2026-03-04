import type { JobCategory, ExperienceLevel } from "@/lib/client";

export interface QualificationFormData {
  id?: string;
  _key?: string;
  category:
    | "skill"
    | "experience"
    | "education"
    | "certification"
    | "tool"
    | "language"
    | "other";
  name: string;
  requirement_level: "required" | "preferred";
  years_required?: number | null;
  proficiency_level?:
    | "beginner"
    | "intermediate"
    | "advanced"
    | "expert"
    | null;
  order: number;
}

export interface QuestionFormData {
  id?: string;
  _key?: string;
  text: string;
  question_type: "text" | "mcq" | "mcq_single";
  order: number;
  choices: string[];
  is_required: boolean;
}

export interface JobProfileFormValues {
  title: string;
  category: string;
  employment_type:
    | "full_time"
    | "part_time"
    | "contract"
    | "internship"
    | "freelance"
    | "not_applicable";
  experience_level: string;
  description: string;
  qualifications: QualificationFormData[];
  questions: QuestionFormData[];
  is_active?: boolean;
}

export interface JobProfileFormProps {
  categories: JobCategory[];
  experienceLevels: ExperienceLevel[];
  initialValues?: Partial<JobProfileFormValues>;
  onSubmit: (values: JobProfileFormValues) => Promise<void>;
  submitLabel?: string;
  isSubmitting?: boolean;
  showIsActive?: boolean;
}
