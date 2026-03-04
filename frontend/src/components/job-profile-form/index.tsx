"use client";

import { useState, useRef, useEffect } from "react";
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
  verticalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";
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
import { Plus, Loader2, ChevronsUpDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { QUALIFICATION_CATEGORY_COLORS } from "@/lib/constants/job-profile";
import { Checkbox } from "@/components/ui/checkbox";

import type {
  JobProfileFormValues,
  JobProfileFormProps,
  QualificationFormData,
  QuestionFormData,
} from "./types";
import {
  DEFAULT_VALUES,
  EMPLOYMENT_TYPE_OPTIONS,
  QUALIFICATION_CATEGORY_OPTIONS,
  PROFICIENCY_LEVEL_OPTIONS,
} from "./constants";
import { SortableQuestionCard } from "./sortable-question-card";
import { Trash2 } from "lucide-react";

// Re-export types so existing imports keep working
export type {
  QualificationFormData,
  QuestionFormData,
  JobProfileFormValues,
} from "./types";

// ---------------------------------------------------------------------------
// JobProfileForm
// ---------------------------------------------------------------------------

export function JobProfileForm({
  categories,
  experienceLevels,
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
      qualifications: (merged.qualifications ?? []).map((q) => ({
        ...q,
        _key: q._key ?? q.id ?? crypto.randomUUID(),
      })),
      questions: (merged.questions ?? []).map((q) => ({
        ...q,
        _key: q._key ?? q.id ?? crypto.randomUUID(),
      })),
    };
  });
  const [categoryOpen, setCategoryOpen] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Refs for qualification name inputs, keyed by _key
  const qualInputRefs = useRef<Record<string, HTMLInputElement | null>>({});
  const pendingFocusKey = useRef<string | null>(null);

  useEffect(() => {
    if (pendingFocusKey.current) {
      qualInputRefs.current[pendingFocusKey.current]?.focus();
      pendingFocusKey.current = null;
    }
  });

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

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

    values.qualifications.forEach((q, i) => {
      if (!q.name.trim()) errs[`qual_${i}_name`] = "Name is required.";
    });

    values.questions.forEach((q, i) => {
      if (!q.text.trim())
        errs[`question_${i}_text`] = "Question text is required.";
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
    const normalized: JobProfileFormValues = {
      ...values,
      qualifications: values.qualifications.map(
        ({ _key: _unused, ...q }, i) => ({ ...q, order: i }),
      ),
      questions: values.questions.map(({ _key: _unused, ...q }, i) => ({
        ...q,
        order: i,
      })),
    };
    await onSubmit(normalized);
  }

  // ─── Qualification helpers ──────────────────────────────────────────────

  function addQualification(
    category: QualificationFormData["category"] = "skill",
  ) {
    const newQ: QualificationFormData = {
      _key: crypto.randomUUID(),
      category,
      name: "",
      requirement_level: "required",
      years_required: null,
      proficiency_level: null,
      order: values.qualifications.length,
    };
    // Insert after the last item of the same category
    const lastIndex = values.qualifications.reduce(
      (last, q, i) => (q.category === category ? i : last),
      -1,
    );
    const updated = [...values.qualifications];
    updated.splice(lastIndex + 1, 0, newQ);
    pendingFocusKey.current = newQ._key!;
    set("qualifications", updated);
  }

  function removeQualification(index: number) {
    set(
      "qualifications",
      values.qualifications.filter((_, i) => i !== index),
    );
  }

  function updateQualification(
    index: number,
    patch: Partial<QualificationFormData>,
  ) {
    const updated = [...values.qualifications];
    updated[index] = { ...updated[index], ...patch };
    set("qualifications", updated);
  }

  // ─── Question helpers ───────────────────────────────────────────────────

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

  // Group qualifications by category for display — include all categories
  const qualsByCategory = QUALIFICATION_CATEGORY_OPTIONS.map((cat) => ({
    ...cat,
    items: values.qualifications
      .map((q, i) => ({ ...q, _index: i }))
      .filter((q) => q.category === cat.value),
  }));

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
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

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {/* Category (combobox) */}
            <div className="space-y-1.5">
              <Label>
                Category <span className="text-destructive">*</span>
              </Label>
              <Popover open={categoryOpen} onOpenChange={setCategoryOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={categoryOpen}
                    className="w-full justify-between font-normal"
                  >
                    {values.category
                      ? (categories.find((c) => c.id === values.category)
                          ?.title ?? "Select category")
                      : "Select category"}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  className="w-[--radix-popover-trigger-width] p-0"
                  align="start"
                >
                  <Command>
                    <CommandInput placeholder="Search category…" />
                    <CommandList>
                      <CommandEmpty>No category found.</CommandEmpty>
                      <CommandGroup>
                        {categories.map((c) => (
                          <CommandItem
                            key={c.id}
                            value={c.title ?? ""}
                            onSelect={() => {
                              set("category", c.id!);
                              setCategoryOpen(false);
                            }}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                values.category === c.id
                                  ? "opacity-100"
                                  : "opacity-0",
                              )}
                            />
                            {c.title}
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
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
          </div>

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

      {/* Description */}
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

      {/* Qualifications */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Qualifications
            {values.qualifications.length > 0 && (
              <Badge variant="secondary" className="ml-2 text-xs font-normal">
                {values.qualifications.length}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Add skills, experience, education, certifications, tools, languages,
            or other qualifications needed for this role. Toggle each as
            required or preferred.
          </p>

          {/* Grouped display — each category always visible with inline add */}
          {qualsByCategory.map((group) => (
            <div key={group.value} className="space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Badge
                  variant="outline"
                  className={cn(
                    "text-xs",
                    QUALIFICATION_CATEGORY_COLORS[group.value],
                  )}
                >
                  {group.label}
                </Badge>
                {group.items.length > 0 && (
                  <span className="text-xs text-muted-foreground">
                    ({group.items.length})
                  </span>
                )}
              </h4>
              {group.items.map((q) => (
                <div
                  key={q._key}
                  className="flex items-center gap-2 rounded-md border p-3"
                >
                  <div className="flex-1 space-y-2">
                    <div className="flex gap-2 items-start">
                      <Input
                        ref={(el) => {
                          qualInputRefs.current[q._key!] = el;
                        }}
                        value={q.name}
                        placeholder={`${group.label} name…`}
                        onChange={(e) =>
                          updateQualification(q._index, {
                            name: e.target.value,
                          })
                        }
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addQualification(
                              group.value as QualificationFormData["category"],
                            );
                          }
                        }}
                        className="flex-1"
                      />
                      <div className="flex items-center gap-1.5">
                        <Checkbox
                          id={`qual_${q._key}_required`}
                          checked={q.requirement_level === "required"}
                          onCheckedChange={(checked) =>
                            updateQualification(q._index, {
                              requirement_level: checked
                                ? "required"
                                : "preferred",
                            })
                          }
                        />
                        <Label
                          htmlFor={`qual_${q._key}_required`}
                          className="text-xs font-normal cursor-pointer"
                        >
                          Required
                        </Label>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="shrink-0 h-9 w-9 text-destructive hover:text-destructive"
                        onClick={() => removeQualification(q._index)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    {errors[`qual_${q._index}_name`] && (
                      <p className="text-xs text-destructive">
                        {errors[`qual_${q._index}_name`]}
                      </p>
                    )}
                    <div className="flex gap-2 flex-wrap">
                      {(q.category === "experience" ||
                        q.category === "skill" ||
                        q.category === "tool") && (
                        <div className="flex items-center gap-1.5">
                          <Label className="text-xs text-muted-foreground whitespace-nowrap">
                            Years:
                          </Label>
                          <Input
                            type="number"
                            min={0}
                            className="w-20 h-8 text-sm"
                            placeholder="—"
                            value={q.years_required ?? ""}
                            onChange={(e) =>
                              updateQualification(q._index, {
                                years_required: e.target.value
                                  ? parseInt(e.target.value)
                                  : null,
                              })
                            }
                          />
                        </div>
                      )}
                      {(q.category === "skill" ||
                        q.category === "tool" ||
                        q.category === "language") && (
                        <div className="flex items-center gap-1.5">
                          <Label className="text-xs text-muted-foreground whitespace-nowrap">
                            Proficiency:
                          </Label>
                          <Select
                            value={q.proficiency_level ?? "none"}
                            onValueChange={(v) =>
                              updateQualification(q._index, {
                                proficiency_level: (v === "none"
                                  ? null
                                  : v) as QualificationFormData["proficiency_level"],
                              })
                            }
                          >
                            <SelectTrigger className="w-36 h-8 text-sm">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {PROFICIENCY_LEVEL_OPTIONS.map((o) => (
                                <SelectItem key={o.value} value={o.value}>
                                  {o.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 text-xs"
                onClick={() =>
                  addQualification(
                    group.value as QualificationFormData["category"],
                  )
                }
              >
                <Plus className="mr-1 h-3 w-3" /> Add {group.label}
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Questions */}
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
            <Plus className="mr-2 h-4 w-4" /> Add Question
          </Button>
        </CardContent>
      </Card>

      {/* Submit */}
      <div className="flex justify-end">
        <Button type="submit" disabled={isSubmitting} className="min-w-32">
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
