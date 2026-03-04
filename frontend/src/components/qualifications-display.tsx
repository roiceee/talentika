import type { Qualification } from "@/lib/client";
import { Badge } from "@/components/ui/badge";
import {
  QUALIFICATION_CATEGORY_LABELS,
  QUALIFICATION_CATEGORY_COLORS,
} from "@/lib/constants/job-profile";

function groupQualifications(qualifications: Qualification[]) {
  const groups: Record<string, Qualification[]> = {};
  for (const q of qualifications) {
    if (!groups[q.category]) groups[q.category] = [];
    groups[q.category].push(q);
  }
  return groups;
}

interface QualificationsDisplayProps {
  qualifications: Qualification[];
  /** Show coloured category badge headers (default: true) */
  showCategoryBadge?: boolean;
}

/**
 * Renders a grouped list of qualifications, used by both the
 * authenticated detail page and the public job page.
 */
export function QualificationsDisplay({
  qualifications,
  showCategoryBadge = true,
}: QualificationsDisplayProps) {
  if (qualifications.length === 0) return null;

  const groups = groupQualifications(qualifications);

  return (
    <div className="space-y-4">
      {Object.entries(groups).map(([cat, items]) => (
        <div key={cat}>
          {showCategoryBadge ? (
            <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
              <Badge
                variant="outline"
                className={`text-xs ${QUALIFICATION_CATEGORY_COLORS[cat] ?? ""}`}
              >
                {QUALIFICATION_CATEGORY_LABELS[cat] ?? cat}
              </Badge>
            </h4>
          ) : (
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
              {QUALIFICATION_CATEGORY_LABELS[cat] ?? cat}
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            {items.map((q) => (
              <Badge
                key={q.id}
                variant={
                  q.requirement_level === "required" ? "default" : "outline"
                }
                className="text-xs"
              >
                {q.name}
                {q.years_required != null && (
                  <span className="ml-1 opacity-70">({q.years_required}y)</span>
                )}
                {q.proficiency_level && (
                  <span className="ml-1 opacity-70">
                    · {q.proficiency_level}
                  </span>
                )}
                {q.requirement_level === "preferred" && (
                  <span className="ml-1 opacity-60">preferred</span>
                )}
              </Badge>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
