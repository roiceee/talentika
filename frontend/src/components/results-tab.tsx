"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import {
  getResultsSummary,
  requestExport,
  pollExport,
  getExportDownloadUrl,
  type ResultsCategory,
} from "@/lib/api";
import type { JobApplicationDetailWithAnalysis } from "@/lib/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Mail,
  User,
  Brain,
  AlertCircle,
  Clock,
  Loader2,
  Download,
  ChevronDown,
  ChevronRight,
  FileSpreadsheet,
  FileText,
} from "lucide-react";

// ─── Config ──────────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<
  string,
  {
    label: string;
    badgeVariant: "default" | "secondary" | "outline" | "destructive";
    badgeClass?: string;
  }
> = {
  to_be_reviewed: {
    label: "To Be Reviewed",
    badgeVariant: "secondary",
    badgeClass: "bg-primary/10 text-primary border-primary/20",
  },
  reviewed: {
    label: "Hold",
    badgeVariant: "default",
    badgeClass: "bg-amber-100 text-amber-800 border-amber-200",
  },
  shortlisted: {
    label: "Shortlisted",
    badgeVariant: "default",
    badgeClass: "bg-emerald-600 text-white hover:bg-emerald-700",
  },
  rejected: { label: "Rejected", badgeVariant: "destructive" },
};

const ANALYSIS_STATUS_CONFIG: Record<
  string,
  { label: string; icon: typeof Brain; className: string }
> = {
  uploaded: {
    label: "Queued",
    icon: Clock,
    className: "text-muted-foreground",
  },
  ocr_pending: {
    label: "OCR Processing",
    icon: Loader2,
    className: "text-blue-600",
  },
  ocr_done: { label: "OCR Done", icon: Clock, className: "text-blue-600" },
  ai_pending: {
    label: "AI Analyzing",
    icon: Loader2,
    className: "text-blue-600",
  },
  done: { label: "Done", icon: Brain, className: "text-emerald-600" },
  failed: { label: "Failed", icon: AlertCircle, className: "text-destructive" },
};

const SCORE_COLOR_MAP: Record<string, string> = {
  suitable: "bg-emerald-100 text-emerald-800",
  potentially_suitable: "bg-amber-100 text-amber-800",
  unsuitable: "bg-red-100 text-red-800",
};

type AnalysisData = {
  id?: string;
  status?: string;
  score?: number | null;
  score_category?: { key: string; label: string } | null;
  ai_analysis_summary?: string | null;
};

// ─── Props ────────────────────────────────────────────────────────────────────

interface ResultsTabProps {
  orgId: string;
  jobProfileId: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function ResultsTab({ orgId, jobProfileId }: ResultsTabProps) {
  const router = useRouter();

  const [categories, setCategories] = useState<ResultsCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedStatuses, setExpandedStatuses] = useState<Set<string>>(
    new Set(),
  );
  const [exportingStatuses, setExportingStatuses] = useState<
    Map<string, { id: string; format: string }>
  >(new Map());

  // Fetch results summary
  const fetchResults = useCallback(async () => {
    try {
      const result = await getResultsSummary(orgId, jobProfileId);
      setCategories(result.categories);
      // Auto-expand statuses that have applications
      setExpandedStatuses((prev) => {
        if (prev.size === 0) {
          return new Set(
            result.categories.filter((c) => c.count > 0).map((c) => c.status),
          );
        }
        return prev;
      });
    } catch (error) {
      if (error instanceof AxiosError && error.response?.status === 403) {
        toast.error("You don't have permission to view results");
      } else {
        toast.error("Failed to load results");
      }
    } finally {
      setIsLoading(false);
    }
  }, [orgId, jobProfileId]);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  // Toggle category expansion
  const toggleExpanded = useCallback((status: string) => {
    setExpandedStatuses((prev) => {
      const next = new Set(prev);
      if (next.has(status)) {
        next.delete(status);
      } else {
        next.add(status);
      }
      return next;
    });
  }, []);

  // Export handler with polling
  const pollIntervalRef = useRef<Map<string, ReturnType<typeof setInterval>>>(
    new Map(),
  );

  useEffect(() => {
    const intervals = pollIntervalRef.current;
    return () => {
      // Cleanup poll intervals on unmount
      intervals.forEach((interval) => clearInterval(interval));
    };
  }, []);

  const handleExport = useCallback(
    async (applicationStatus: string, format: "csv" | "xlsx") => {
      const key = `${applicationStatus}_${format}`;
      if (exportingStatuses.has(key)) return;

      try {
        const job = await requestExport(orgId, jobProfileId, {
          application_status: applicationStatus || undefined,
          format,
        });

        setExportingStatuses((prev) => {
          const next = new Map(prev);
          next.set(key, { id: job.id, format });
          return next;
        });

        // Start polling
        const interval = setInterval(async () => {
          try {
            const status = await pollExport(orgId, jobProfileId, job.id);
            if (status.status === "done") {
              clearInterval(interval);
              pollIntervalRef.current.delete(key);
              setExportingStatuses((prev) => {
                const next = new Map(prev);
                next.delete(key);
                return next;
              });

              // Trigger download
              const url = getExportDownloadUrl(orgId, jobProfileId, job.id);
              const a = document.createElement("a");
              a.href = url;
              a.download = "";
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              toast.success("Export ready — downloading now");
            } else if (status.status === "failed") {
              clearInterval(interval);
              pollIntervalRef.current.delete(key);
              setExportingStatuses((prev) => {
                const next = new Map(prev);
                next.delete(key);
                return next;
              });
              toast.error(
                status.error_message ?? "Export failed. Please try again.",
              );
            }
          } catch {
            clearInterval(interval);
            pollIntervalRef.current.delete(key);
            setExportingStatuses((prev) => {
              const next = new Map(prev);
              next.delete(key);
              return next;
            });
            toast.error("Failed to check export status");
          }
        }, 2000);

        pollIntervalRef.current.set(key, interval);
      } catch {
        toast.error("Failed to start export");
      }
    },
    [orgId, jobProfileId, exportingStatuses],
  );

  // Navigate to application detail
  const goToApplication = useCallback(
    (applicationId: string) => {
      router.push(
        `/job-profiles/${jobProfileId}/applications/${applicationId}`,
      );
    },
    [router, jobProfileId],
  );

  // ─── Loading ──────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  const totalApplications = categories.reduce((sum, c) => sum + c.count, 0);

  const PENDING_ANALYSIS_STATUSES = new Set([
    "uploaded",
    "ocr_pending",
    "ocr_done",
    "ai_pending",
  ]);
  const hasPendingAnalysis = categories.some((c) =>
    c.preview.some((app) => {
      const analysis = (app.analysis ?? null) as AnalysisData | null;
      return analysis?.status && PENDING_ANALYSIS_STATUSES.has(analysis.status);
    }),
  );

  if (totalApplications === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">
            No applications have been submitted yet.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {totalApplications} total application
          {totalApplications !== 1 ? "s" : ""}
        </p>
        <ExportDropdown
          label="Export All"
          isExporting={(fmt) => exportingStatuses.has(`_${fmt}`)}
          onExport={(fmt) => handleExport("", fmt)}
          disabledReason={
            hasPendingAnalysis
              ? "Some applications are still being processed. Wait for all analyses to complete before exporting."
              : undefined
          }
        />
      </div>

      {/* Status categories */}
      {categories.map((category) => {
        const config = STATUS_CONFIG[category.status] ?? {
          label: category.label,
          badgeVariant: "outline" as const,
        };
        const isExpanded = expandedStatuses.has(category.status);

        return (
          <Card key={category.status} className="overflow-hidden">
            <CardHeader
              className="cursor-pointer select-none py-3 hover:bg-muted/30 transition-colors"
              onClick={() => toggleExpanded(category.status)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  )}
                  <CardTitle className="text-sm font-semibold">
                    {config.label}
                  </CardTitle>
                  <Badge
                    variant={config.badgeVariant}
                    className={`text-xs ${config.badgeClass ?? ""}`}
                  >
                    {category.count}
                  </Badge>
                </div>
                {category.count > 0 && (
                  <div onClick={(e) => e.stopPropagation()}>
                    <ExportDropdown
                      label="Export"
                      isExporting={(fmt) =>
                        exportingStatuses.has(`${category.status}_${fmt}`)
                      }
                      onExport={(fmt) => handleExport(category.status, fmt)}
                      disabledReason={
                        hasPendingAnalysis
                          ? "Some applications are still being processed. Wait for all analyses to complete before exporting."
                          : undefined
                      }
                    />
                  </div>
                )}
              </div>
            </CardHeader>

            {isExpanded && category.count > 0 && (
              <CardContent className="pt-0">
                <PreviewTable
                  applications={category.preview}
                  onRowClick={goToApplication}
                  highlightStatus="shortlisted"
                />
                {category.count > category.preview.length && (
                  <p className="mt-3 text-xs text-muted-foreground text-center">
                    Showing {category.preview.length} of {category.count}{" "}
                    applications. Export for the full list.
                  </p>
                )}
              </CardContent>
            )}

            {isExpanded && category.count === 0 && (
              <CardContent className="pt-0">
                <p className="text-sm text-muted-foreground py-4 text-center">
                  No applications in this category.
                </p>
              </CardContent>
            )}
          </Card>
        );
      })}
    </div>
  );
}

// ─── Export dropdown ──────────────────────────────────────────────────────────

function ExportDropdown({
  label,
  isExporting,
  onExport,
  disabledReason,
}: {
  label: string;
  isExporting: (format: "csv" | "xlsx") => boolean;
  onExport: (format: "csv" | "xlsx") => void;
  disabledReason?: string;
}) {
  const csvBusy = isExporting("csv");
  const xlsxBusy = isExporting("xlsx");
  const anyBusy = csvBusy || xlsxBusy;
  const isDisabled = anyBusy || !!disabledReason;

  const trigger = (
    <Button variant="outline" size="sm" disabled={isDisabled}>
      {anyBusy ? (
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      ) : (
        <Download className="mr-2 h-4 w-4" />
      )}
      {anyBusy ? "Exporting…" : label}
    </Button>
  );

  return (
    <DropdownMenu>
      {disabledReason && !anyBusy ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <span tabIndex={0}>{trigger}</span>
          </TooltipTrigger>
          <TooltipContent side="left" className="max-w-64">
            {disabledReason}
          </TooltipContent>
        </Tooltip>
      ) : (
        <DropdownMenuTrigger asChild>{trigger}</DropdownMenuTrigger>
      )}
      <DropdownMenuContent align="end">
        <DropdownMenuItem disabled={csvBusy} onClick={() => onExport("csv")}>
          <FileText className="mr-2 h-4 w-4" />
          CSV
        </DropdownMenuItem>
        <DropdownMenuItem disabled={xlsxBusy} onClick={() => onExport("xlsx")}>
          <FileSpreadsheet className="mr-2 h-4 w-4" />
          XLSX
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// ─── Preview table ───────────────────────────────────────────────────────────

function PreviewTable({
  applications,
  onRowClick,
  highlightStatus,
}: {
  applications: JobApplicationDetailWithAnalysis[];
  onRowClick: (id: string) => void;
  highlightStatus?: string;
}) {
  return (
    <div className="rounded-lg border overflow-hidden">
      <Table>
        <TableHeader className="bg-muted/40">
          <TableRow className="hover:bg-transparent border-b border-border/60">
            <TableHead className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Applicant</TableHead>
            <TableHead className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Contact</TableHead>
            <TableHead className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">AI Analysis</TableHead>
            <TableHead className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Score</TableHead>
            <TableHead className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Submitted</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {applications.map((app) => {
            const analysis = (app.analysis ??
              null) as unknown as AnalysisData | null;
            const isHighlighted = highlightStatus && app.status === highlightStatus;

            return (
              <TableRow
                key={app.id}
                className={`cursor-pointer transition-colors ${isHighlighted ? "bg-emerald-50 hover:bg-emerald-100" : "hover:bg-primary/4"}`}
                onClick={() => app.id && onRowClick(app.id)}
              >
                {/* Applicant */}
                <TableCell>
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 shrink-0">
                      <User className="h-3.5 w-3.5 text-primary" />
                    </div>
                    <span className="font-medium text-sm">
                      {app.first_name} {app.last_name}
                    </span>
                  </div>
                </TableCell>

                {/* Contact */}
                <TableCell>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Mail className="h-3.5 w-3.5" />
                      {app.email}
                    </span>
                  </div>
                </TableCell>

                {/* AI Analysis Status */}
                <TableCell>
                  <AnalysisStatusBadge analysis={analysis} />
                </TableCell>

                {/* Score */}
                <TableCell>
                  <ScoreBadge analysis={analysis} />
                </TableCell>

                {/* Submitted */}
                <TableCell>
                  {app.submitted_at ? (
                    <span className="text-sm text-muted-foreground">
                      {new Date(app.submitted_at).toLocaleDateString(
                        undefined,
                        {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        },
                      )}
                    </span>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

// ─── Inline helpers ──────────────────────────────────────────────────────────

function AnalysisStatusBadge({ analysis }: { analysis: AnalysisData | null }) {
  if (!analysis?.status) {
    return <span className="text-xs text-muted-foreground">No analysis</span>;
  }
  const cfg = ANALYSIS_STATUS_CONFIG[analysis.status];
  if (!cfg) {
    return (
      <Badge variant="outline" className="text-xs">
        {analysis.status}
      </Badge>
    );
  }
  const Icon = cfg.icon;
  const isSpinning = ["ocr_pending", "ai_pending"].includes(analysis.status);
  return (
    <span
      className={`flex items-center gap-1.5 text-xs font-medium ${cfg.className}`}
    >
      <Icon className={`h-3.5 w-3.5 ${isSpinning ? "animate-spin" : ""}`} />
      {cfg.label}
    </span>
  );
}

function ScoreBadge({ analysis }: { analysis: AnalysisData | null }) {
  if (analysis?.status !== "done" || !analysis?.score_category) {
    return <span className="text-xs text-muted-foreground">—</span>;
  }
  const cat = analysis.score_category;
  return (
    <Badge
      variant="secondary"
      className={`text-xs font-semibold ${SCORE_COLOR_MAP[cat.key] ?? ""}`}
    >
      {cat.label}
      {analysis.score != null && (
        <span className="ml-1 opacity-70">({analysis.score})</span>
      )}
    </Badge>
  );
}
