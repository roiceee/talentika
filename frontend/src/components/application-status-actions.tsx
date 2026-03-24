"use client";

import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ApplicationStatusActionsProps {
  currentStatus: string | undefined;
  isUpdating: boolean;
  /** Called with the target status and whether to also navigate to next */
  onAction: (status: string, andNext: boolean) => void;
  /** Stack buttons vertically (for FAB panel) */
  vertical?: boolean;
}

const ACTIONS = [
  {
    status: "rejected",
    label: "Reject",
    active: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    inactive: "border-destructive/40 text-destructive hover:bg-destructive/10",
  },
  {
    status: "reviewed",
    label: "Hold",
    active: "bg-amber-500 text-white hover:bg-amber-600",
    inactive: "",
  },
  {
    status: "shortlisted",
    label: "Shortlist",
    active: "bg-emerald-600 text-white hover:bg-emerald-700",
    inactive: "border-emerald-500/40 text-emerald-700 hover:bg-emerald-50",
  },
] as const;

export function ApplicationStatusActions({
  currentStatus,
  isUpdating,
  onAction,
  vertical = false,
}: ApplicationStatusActionsProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className={`flex gap-1.5 ${vertical ? "flex-col" : "flex-row"}`}>
        {ACTIONS.map(({ status, label, active, inactive }) => {
          const isActive = currentStatus === status;
          return (
            <Button
              key={status}
              size="sm"
              variant="outline"
              className={`${vertical ? "w-full" : ""} ${isActive ? active : inactive} transition-colors`}
              disabled={isUpdating}
              onClick={(e) => onAction(status, e.ctrlKey || e.metaKey)}
            >
              {isUpdating && isActive ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
              ) : null}
              {label}
            </Button>
          );
        })}
      </div>
      <p className="text-xs text-muted-foreground flex items-center gap-1">
        <kbd className="pointer-events-none inline-flex h-4 select-none items-center rounded border bg-muted px-1 font-mono text-[10px] font-medium text-muted-foreground">
          Ctrl
        </kbd>
        <span>+ click to apply &amp; go next</span>
      </p>
    </div>
  );
}
