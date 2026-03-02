import type { Question } from "@/lib/client";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

export function QuestionField({
  question,
  textValue,
  mcqValues,
  onTextChange,
  onMcqToggle,
  onMcqSingleSelect,
}: {
  question: Question;
  textValue: string;
  mcqValues: string[];
  onTextChange: (v: string) => void;
  onMcqToggle: (choice: string) => void;
  onMcqSingleSelect: (choice: string) => void;
}) {
  const q = question;
  const isRequired = q.is_required ?? false;

  return (
    <div className="space-y-2">
      <Label>
        {q.text}
        {isRequired && <span className="text-destructive ml-1">*</span>}
      </Label>

      {q.question_type === "text" && (
        <Textarea
          value={textValue}
          onChange={(e) => onTextChange(e.target.value)}
          placeholder="Your answer..."
          required={isRequired}
        />
      )}

      {q.question_type === "mcq" && q.choices && (
        <div className="space-y-2 pl-1">
          {q.choices.map((choice) => (
            <label
              key={choice}
              className="flex items-center gap-2 text-sm cursor-pointer"
            >
              <Checkbox
                checked={mcqValues.includes(choice)}
                onCheckedChange={() => onMcqToggle(choice)}
              />
              {choice}
            </label>
          ))}
        </div>
      )}

      {q.question_type === "mcq_single" && q.choices && (
        <RadioGroup
          value={mcqValues[0] ?? ""}
          onValueChange={(v) => onMcqSingleSelect(v)}
          required={isRequired}
        >
          {q.choices.map((choice) => (
            <label
              key={choice}
              className="flex items-center gap-2 text-sm cursor-pointer"
            >
              <RadioGroupItem value={choice} />
              {choice}
            </label>
          ))}
        </RadioGroup>
      )}
    </div>
  );
}
