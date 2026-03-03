"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import { listJobApplications, retryAnalysis } from "@/lib/api";
import type { JobApplicationDetailWithAnalysis } from "@/lib/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
  Mail,
  Phone,
  FileText,
  User,
  RefreshCw,
  Loader2,
  Brain,
  AlertCircle,
  Clock,
} from "lucide-react";

const STATUS_CONFIG: Record<
  string,
  {
    label: string;
    variant: "default" | "secondary" | "outline" | "destructive";
    className?: string;
  }
> = {
  to_be_reviewed: { label: "To Be Reviewed", variant: "secondary" },
  reviewed: { label: "Reviewed", variant: "default" },
  shortlisted: {
    label: "Shortlisted",
    variant: "default",
    className: "bg-emerald-600 text-white hover:bg-emerald-700",
  },
  rejected: { label: "Rejected", variant: "destructive" },
};

type AnalysisData = {
  id?: string;
  status?: string;
  score?: number | null;
  ai_analysis_summary?: string;
  error_message?: string;
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

interface ApplicationsTabProps {
  orgId: string;
  jobProfileId: string;
}

export function ApplicationsTab({ orgId, jobProfileId }: ApplicationsTabProps) {
  const router = useRouter();
  const [applications, setApplications] = useState<
    JobApplicationDetailWithAnalysis[]
  >([]);
  const [isLoading, setIsLoading] = useState(true);
  const [retryingIds, setRetryingIds] = useState<Set<string>>(new Set());

  const fetchApplications = useCallback(async () => {
    try {
      const data = await listJobApplications(orgId, jobProfileId);
      setApplications(data);
    } catch (error) {
      if (error instanceof AxiosError && error.response?.status === 403) {
        toast.error("You don't have permission to view applications");
      } else {
        toast.error("Failed to load applications");
      }
    } finally {
      setIsLoading(false);
    }
  }, [orgId, jobProfileId]);

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

  // Poll every 5 seconds while any analysis is still processing
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const hasProcessing = applications.some((app) => {
      const a = (app.analysis ?? null) as unknown as AnalysisData | null;
      return a?.status && !["done", "failed"].includes(a.status);
    });

    if (hasProcessing) {
      if (!pollRef.current) {
        pollRef.current = setInterval(() => {
          fetchApplications();
        }, 5000);
      }
    } else if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [applications, fetchApplications]);

  async function handleRetry(e: React.MouseEvent, applicationId: string) {
    e.stopPropagation();
    setRetryingIds((prev) => new Set(prev).add(applicationId));
    try {
      await retryAnalysis(applicationId);
      toast.success("Analysis re-triggered");
      // Update the local state to reflect queued status
      setApplications((prev) =>
        prev.map((app) =>
          app.id === applicationId
            ? {
                ...app,
                analysis: JSON.stringify({
                  ...(typeof app.analysis === "string"
                    ? {}
                    : (app.analysis as unknown as AnalysisData)),
                  status: "uploaded",
                  error_message: "",
                }),
              }
            : app,
        ),
      );
    } catch {
      toast.error("Failed to retry analysis");
    } finally {
      setRetryingIds((prev) => {
        const next = new Set(prev);
        next.delete(applicationId);
        return next;
      });
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  if (applications.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <FileText className="h-12 w-12 text-muted-foreground/40 mb-4" />
          <h3 className="text-lg font-medium mb-1">No applications yet</h3>
          <p className="text-sm text-muted-foreground">
            Applications will appear here once candidates apply for this job
            profile.
          </p>
        </CardContent>
      </Card>
    );
  }

  // ─── List view ───────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {applications.length} application{applications.length !== 1 && "s"}
        </p>
      </div>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Applicant</TableHead>
              <TableHead>Contact</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>AI Analysis</TableHead>
              <TableHead>Score</TableHead>
              <TableHead>Submitted</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {applications.map((app) => {
              const statusConfig =
                STATUS_CONFIG[app.status ?? "to_be_reviewed"];
              const analysis = (app.analysis ??
                null) as unknown as AnalysisData | null;
              const analysisStatus = analysis?.status;
              const analysisConfig = analysisStatus
                ? ANALYSIS_STATUS_CONFIG[analysisStatus]
                : null;
              const isProcessing =
                analysisStatus === "ocr_pending" ||
                analysisStatus === "ai_pending";
              return (
                <TableRow
                  key={app.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() =>
                    router.push(
                      `/job-profiles/${jobProfileId}/applications/${app.id}`,
                    )
                  }
                >
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                        <User className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">
                          {app.first_name} {app.last_name}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                        <Mail className="h-3.5 w-3.5" />
                        {app.email}
                      </div>
                      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                        <Phone className="h-3.5 w-3.5" />
                        {app.phone}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={statusConfig?.variant ?? "secondary"}
                      className={statusConfig?.className}
                    >
                      {statusConfig?.label ?? app.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {analysisConfig ? (
                      <div className="flex items-center gap-1.5">
                        {isProcessing ? (
                          <Loader2
                            className={`h-3.5 w-3.5 animate-spin ${analysisConfig.className}`}
                          />
                        ) : (
                          <analysisConfig.icon
                            className={`h-3.5 w-3.5 ${analysisConfig.className}`}
                          />
                        )}
                        <span
                          className={`text-xs font-medium ${analysisConfig.className}`}
                        >
                          {analysisConfig.label}
                        </span>
                        {analysisStatus === "failed" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-1.5 text-xs"
                            disabled={retryingIds.has(app.id ?? "")}
                            onClick={(e) => handleRetry(e, app.id ?? "")}
                          >
                            {retryingIds.has(app.id ?? "") ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <RefreshCw className="h-3 w-3" />
                            )}
                          </Button>
                        )}
                        {/* Allow retry for stuck processing states */}
                        {analysisStatus &&
                          !["done", "failed"].includes(analysisStatus) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 px-1.5 text-xs text-muted-foreground"
                              title="Retry (stuck?)"
                              disabled={retryingIds.has(app.id ?? "")}
                              onClick={(e) => handleRetry(e, app.id ?? "")}
                            >
                              {retryingIds.has(app.id ?? "") ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <RefreshCw className="h-3 w-3" />
                              )}
                            </Button>
                          )}
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {analysisStatus === "done" && analysis?.score != null ? (
                      <span
                        className={`text-sm font-semibold ${
                          analysis.score >= 70
                            ? "text-emerald-600"
                            : analysis.score >= 40
                              ? "text-amber-600"
                              : "text-destructive"
                        }`}
                      >
                        {analysis.score}/100
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {app.submitted_at
                      ? new Date(app.submitted_at).toLocaleDateString(
                          undefined,
                          {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                          },
                        )
                      : "—"}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
