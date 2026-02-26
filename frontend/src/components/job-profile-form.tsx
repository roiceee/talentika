"use client";

import { useState } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import { Plus, Trash2, GripVertical, Loader2 } from "lucide-react";
import type {
  JobCategory,
  ExperienceLevel,
  AiScreeningConfiguration,
} from "@/lib/client";

// ---------------------------------------------------------------------------
// Local types
// ---------------------------------------------------------------------------

export interface QuestionFormData {
  id?: string;
  /** Stable key used by DnD — never sent to the server. */
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
  requirements: string[];
  ai_screening_configuration: string | null;
  questions: QuestionFormData[];
  is_active?: boolean;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface JobProfileFormProps {
  categories: JobCategory[];
  experienceLevels: ExperienceLevel[];
  aiScreeningConfigs: AiScreeningConfiguration[];
  initialValues?: Partial<JobProfileFormValues>;
  onSubmit: (values: JobProfileFormValues) => Promise<void>;
  submitLabel?: string;
  isSubmitting?: boolean;
  showIsActive?: boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_VALUES: JobProfileFormValues = {
  title: "",
  category: "",
  employment_type: "full_time",
  experience_level: "",
  description: "",
  requirements: [],
  ai_screening_configuration: null,
  questions: [],
  is_active: true,
};

const EMPLOYMENT_TYPE_OPTIONS = [
  { value: "full_time", label: "Full Time" },
  { value: "part_time", label: "Part Time" },
  { value: "contract", label: "Contract" },
  { value: "internship", label: "Internship" },
  { value: "freelance", label: "Freelance" },
  { value: "not_applicable", label: "Not Applicable" },
] as const;

const QUESTION_TYPE_OPTIONS = [
  { value: "text", label: "Text (free-form)" },
  { value: "mcq", label: "Multiple Choice (multi-select)" },
  { value: "mcq_single", label: "Multiple Choice (single select)" },
] as const;

// ---------------------------------------------------------------------------
// SortableQuestionCard
// ---------------------------------------------------------------------------

interface SortableQuestionCardProps {
  q: QuestionFormData;
  qi: number;
  errors: Record<string, string>;
  onUpdate: (patch: Partial<QuestionFormData>) => void;
  onRemove: () => void;
  onAddChoice: () => void;
  onUpdateChoice: (ci: number, value: string) => void;
  onRemoveChoice: (ci: number) => void;
}

function SortableQuestionCard({
  q,
  qi,
  errors,
  onUpdate,
  onRemove,
  onAddChoice,
  onUpdateChoice,
  onRemoveChoice,
}: SortableQuestionCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: q._key! });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
    position: isDragging ? "relative" : undefined,
    zIndex: isDragging ? 50 : undefined,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="rounded-lg border bg-card p-4 space-y-3 shadow-sm"
    >
      {/* Question header */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          {...listeners}
          {...attributes}
          className="cursor-grab active:cursor-grabbing touch-none text-muted-foreground hover:text-foreground focus:outline-none"
          aria-label="Drag to reorder"
        >
          <GripVertical className="h-4 w-4" />
        </button>
        <span className="text-sm font-medium flex-1">Question {qi + 1}</span>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-destructive hover:text-destructive"
          onClick={onRemove}
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>

      <Separator />

      {/* Question text */}
      <div className="space-y-1.5">
        <Label>Question Text *</Label>
        <Textarea
          rows={2}
          placeholder="Enter your question…"
          value={q.text}
          onChange={(e) => onUpdate({ text: e.target.value })}
        />
        {errors[`question_${qi}_text`] && (
          <p className="text-xs text-destructive">
            {errors[`question_${qi}_text`]}
          </p>
        )}
      </div>

      {/* Question type */}
      <div className="space-y-1.5">
        <Label>Question Type</Label>
        <RadioGroup
          value={q.question_type}
          onValueChange={(v: string) =>
            onUpdate({
              question_type: v as QuestionFormData["question_type"],
              ...(v === "text" ? { choices: [] } : {}),
            })
          }
          className="flex flex-wrap gap-4"
        >
          {QUESTION_TYPE_OPTIONS.map((opt) => (
            <div key={opt.value} className="flex items-center space-x-2">
              <RadioGroupItem
                value={opt.value}
                id={`q${q._key}_${opt.value}`}
              />
              <Label
                htmlFor={`q${q._key}_${opt.value}`}
                className="cursor-pointer font-normal"
              >
                {opt.label}
              </Label>
            </div>
          ))}
        </RadioGroup>
      </div>

      {/* Choices (MCQ only) */}
      {(q.question_type === "mcq" || q.question_type === "mcq_single") && (
        <div className="space-y-2">
          <Label>Choices</Label>
          {q.choices.map((choice, ci) => (
            <div key={ci} className="flex gap-2">
              <Input
                value={choice}
                placeholder={`Choice ${ci + 1}`}
                onChange={(e) => onUpdateChoice(ci, e.target.value)}
                className="flex-1"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="shrink-0 text-destructive hover:text-destructive"
                onClick={() => onRemoveChoice(ci)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onAddChoice}
          >
            <Plus className="mr-1 h-3 w-3" />
            Add choice
          </Button>
          {errors[`question_${qi}_choices`] && (
            <p className="text-xs text-destructive">
              {errors[`question_${qi}_choices`]}
            </p>
          )}
        </div>
      )}

      {/* is_required */}
      <div className="flex items-center gap-2">
        <Checkbox
          id={`q${q._key}_required`}
          checked={q.is_required}
          onCheckedChange={(v: boolean | "indeterminate") =>
            onUpdate({ is_required: v === true })
          }
        />
        <Label
          htmlFor={`q${q._key}_required`}
          className="cursor-pointer font-normal"
        >
          Required
        </Label>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// JobProfileForm
// ---------------------------------------------------------------------------

export function JobProfileForm({
  categories,
  experienceLevels,
  aiScreeningConfigs,
  initialValues,
  onSubmit,
  submitLabel = "Save",
  isSubmitting = false,
  showIsActive = false,
}: JobProfileFormProps) {
  const [values, setValues] = useState<JobProfileFormValues>(() => {
    const merged = { ...DEFAULT_VALUES, ...initialValues };
    return {
      ...merged,
      // Ensure every question has a stable _key for DnD
      questions: (merged.questions ?? []).map((q) => ({
        ...q,
        _key: q._key ?? q.id ?? crypto.randomUUID(),
      })),
    };
  });
  const [newRequirement, setNewRequirement] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------

  function set<K extends keyof JobProfileFormValues>(
    key: K,
    value: JobProfileFormValues[K],
  ) {
    setValues((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => ({ ...prev, [key]: "" }));
  }

  function validate(): boolean {
    const errs: Record<string, string> = {};
    if (!values.title.trim()) errs.title = "Title is required.";
    if (!values.category) errs.category = "Category is required.";
    if (!values.experience_level)
      errs.experience_level = "Experience level is required.";
    if (!values.description.trim())
      errs.description = "Description is required.";

    values.questions.forEach((q, i) => {
      if (!q.text.trim()) {
        errs[`question_${i}_text`] = "Question text is required.";
      }
      if (
        (q.question_type === "mcq" || q.question_type === "mcq_single") &&
        q.choices.filter((c) => c.trim()).length === 0
      ) {
        errs[`question_${i}_choices`] =
          "Multiple choice questions must have at least one choice.";
      }
    });

    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    // Re-index question orders and strip _key before submitting
    const normalized: JobProfileFormValues = {
      ...values,
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      questions: values.questions.map(({ _key: _k, ...q }, i) => ({
        ...q,
        order: i,
      })),
      requirements: values.requirements.filter((r) => r.trim()),
    };

    await onSubmit(normalized);
  }

  // -------------------------------------------------------------------------
  // Requirements
  // -------------------------------------------------------------------------

  function addRequirement() {
    const trimmed = newRequirement.trim();
    if (!trimmed) return;
    set("requirements", [...values.requirements, trimmed]);
    setNewRequirement("");
  }

  function removeRequirement(index: number) {
    set(
      "requirements",
      values.requirements.filter((_, i) => i !== index),
    );
  }

  function updateRequirement(index: number, value: string) {
    const updated = [...values.requirements];
    updated[index] = value;
    set("requirements", updated);
  }

  // -------------------------------------------------------------------------
  // Questions
  // -------------------------------------------------------------------------

  function addQuestion() {
    const newQ: QuestionFormData = {
      _key: crypto.randomUUID(),
      text: "",
      question_type: "text",
      order: values.questions.length,
      choices: [],
      is_required: true,
    };
    set("questions", [...values.questions, newQ]);
  }

  function removeQuestion(index: number) {
    set(
      "questions",
      values.questions.filter((_, i) => i !== index),
    );
  }

  function updateQuestion(index: number, patch: Partial<QuestionFormData>) {
    const updated = [...values.questions];
    updated[index] = { ...updated[index], ...patch };
    set("questions", updated);
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = values.questions.findIndex((q) => q._key === active.id);
    const newIndex = values.questions.findIndex((q) => q._key === over.id);
    if (oldIndex === -1 || newIndex === -1) return;
    set("questions", arrayMove(values.questions, oldIndex, newIndex));
  }

  function addChoice(questionIndex: number) {
    const updated = [...values.questions];
    updated[questionIndex] = {
      ...updated[questionIndex],
      choices: [...updated[questionIndex].choices, ""],
    };
    set("questions", updated);
  }

  function updateChoice(
    questionIndex: number,
    choiceIndex: number,
    value: string,
  ) {
    const updated = [...values.questions];
    const choices = [...updated[questionIndex].choices];
    choices[choiceIndex] = value;
    updated[questionIndex] = { ...updated[questionIndex], choices };
    set("questions", updated);
  }

  function removeChoice(questionIndex: number, choiceIndex: number) {
    const updated = [...values.questions];
    updated[questionIndex] = {
      ...updated[questionIndex],
      choices: updated[questionIndex].choices.filter(
        (_, i) => i !== choiceIndex,
      ),
    };
    set("questions", updated);
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* ─── Basic Info ─────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Title */}
          <div className="space-y-1.5">
            <Label htmlFor="title">
              Job Title <span className="text-destructive">*</span>
            </Label>
            <Input
              id="title"
              placeholder="e.g. Senior Software Engineer"
              value={values.title}
              onChange={(e) => set("title", e.target.value)}
            />
            {errors.title && (
              <p className="text-xs text-destructive">{errors.title}</p>
            )}
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {/* Category */}
            <div className="space-y-1.5">
              <Label>
                Category <span className="text-destructive">*</span>
              </Label>
              <Select
                value={values.category}
                onValueChange={(v) => set("category", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((c) => (
                    <SelectItem key={c.id} value={c.id!}>
                      {c.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.category && (
                <p className="text-xs text-destructive">{errors.category}</p>
              )}
            </div>

            {/* Experience Level */}
            <div className="space-y-1.5">
              <Label>
                Experience Level <span className="text-destructive">*</span>
              </Label>
              <Select
                value={values.experience_level}
                onValueChange={(v) => set("experience_level", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select experience level" />
                </SelectTrigger>
                <SelectContent>
                  {experienceLevels.map((l) => (
                    <SelectItem key={l.id} value={l.id!}>
                      {l.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.experience_level && (
                <p className="text-xs text-destructive">
                  {errors.experience_level}
                </p>
              )}
            </div>

            {/* Employment Type */}
            <div className="space-y-1.5">
              <Label>Employment Type</Label>
              <Select
                value={values.employment_type}
                onValueChange={(v) =>
                  set(
                    "employment_type",
                    v as JobProfileFormValues["employment_type"],
                  )
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EMPLOYMENT_TYPE_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* AI Screening Config */}
            <div className="space-y-1.5">
              <Label>AI Screening Configuration</Label>
              <Select
                value={values.ai_screening_configuration ?? "__none__"}
                onValueChange={(v) =>
                  set("ai_screening_configuration", v === "__none__" ? null : v)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="None" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">None</SelectItem>
                  {aiScreeningConfigs.map((c) => (
                    <SelectItem key={c.id} value={c.id!}>
                      {c.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* is_active toggle (edit mode only) */}
          {showIsActive && (
            <div className="flex items-center gap-3">
              <Switch
                id="is_active"
                checked={values.is_active ?? true}
                onCheckedChange={(v: boolean) => set("is_active", v)}
              />
              <Label htmlFor="is_active" className="cursor-pointer">
                Active
              </Label>
              {values.is_active ? (
                <Badge variant="secondary" className="text-xs">
                  Accepting applications
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="text-xs text-muted-foreground"
                >
                  Inactive
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ─── Description ────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Description</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-1.5">
            <Label htmlFor="description">
              Job Description <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="description"
              placeholder="Describe the role, responsibilities, and what you're looking for…"
              rows={6}
              value={values.description}
              onChange={(e) => set("description", e.target.value)}
            />
            {errors.description && (
              <p className="text-xs text-destructive">{errors.description}</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* ─── Requirements ───────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Requirements</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {values.requirements.map((req, i) => (
            <div key={i} className="flex gap-2">
              <Input
                value={req}
                onChange={(e) => updateRequirement(i, e.target.value)}
                placeholder={`Requirement ${i + 1}`}
                className="flex-1"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => removeRequirement(i)}
                className="shrink-0 text-destructive hover:text-destructive"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}

          <div className="flex gap-2">
            <Input
              value={newRequirement}
              onChange={(e) => setNewRequirement(e.target.value)}
              placeholder="Add a requirement…"
              className="flex-1"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addRequirement();
                }
              }}
            />
            <Button type="button" variant="outline" onClick={addRequirement}>
              <Plus className="mr-1 h-4 w-4" />
              Add
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ─── Questions ──────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Application Questions
            {values.questions.length > 0 && (
              <Badge variant="secondary" className="ml-2 text-xs font-normal">
                {values.questions.length}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {values.questions.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No questions yet. Add questions to collect specific information
              from applicants.
            </p>
          )}

          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={values.questions.map((q) => q._key!)}
              strategy={verticalListSortingStrategy}
            >
              <div className="space-y-3">
                {values.questions.map((q, qi) => (
                  <SortableQuestionCard
                    key={q._key!}
                    q={q}
                    qi={qi}
                    errors={errors}
                    onUpdate={(patch) => updateQuestion(qi, patch)}
                    onRemove={() => removeQuestion(qi)}
                    onAddChoice={() => addChoice(qi)}
                    onUpdateChoice={(ci, v) => updateChoice(qi, ci, v)}
                    onRemoveChoice={(ci) => removeChoice(qi, ci)}
                  />
                ))}
              </div>
            </SortableContext>
          </DndContext>

          <Button
            type="button"
            variant="outline"
            className="w-full"
            onClick={addQuestion}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Question
          </Button>
        </CardContent>
      </Card>

      {/* ─── Submit ─────────────────────────────────────────────────────── */}
      <div className="flex justify-end">
        <Button type="submit" disabled={isSubmitting} className="min-w-32">
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
