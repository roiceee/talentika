"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import { Trash2, GripVertical, Plus } from "lucide-react";
import type { QuestionFormData } from "./types";
import { QUESTION_TYPE_OPTIONS } from "./constants";

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

export function SortableQuestionCard({
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
            <Plus className="mr-1 h-3 w-3" /> Add choice
          </Button>
          {errors[`question_${qi}_choices`] && (
            <p className="text-xs text-destructive">
              {errors[`question_${qi}_choices`]}
            </p>
          )}
        </div>
      )}

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
