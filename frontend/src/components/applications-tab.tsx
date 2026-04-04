"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import {
  listJobApplications,
  retryAnalysis,
  deleteJobApplication,
  getJobProfileAnalytics,
  type PaginatedApplications,
} from "@/lib/api";
import type { JobApplicationDetailWithAnalysis } from "@/lib/client";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  type SortingState,
  type PaginationState,
} from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  SlidersHorizontal,
  Sparkles,
  Star,
  Trash2,
  MoreHorizontal,
} from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// ─── Config ──────────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<
  string,
  {
    label: string;
    variant: "default" | "secondary" | "outline" | "destructive";
    className?: string;
  }
> = {
  to_be_reviewed: {
    label: "To Be Reviewed",
    variant: "outline",
    className: "border-primary/40 text-primary",
  },
  reviewed: {
    label: "Hold",
    variant: "outline",
    className: "border-amber-400 text-amber-700",
  },
  shortlisted: {
    label: "Shortlisted",
    variant: "outline",
    className: "border-emerald-500 text-emerald-700",
  },
  rejected: {
    label: "Rejected",
    variant: "outline",
    className: "border-red-400 text-red-600",
  },
};

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "to_be_reviewed", label: "To Be Reviewed" },
  { value: "reviewed", label: "Hold" },
  { value: "shortlisted", label: "Shortlisted" },
  { value: "rejected", label: "Rejected" },
];

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

type AnalysisData = {
  id?: string;
  status?: string;
  score_category?: { key: string; label: string } | null;
  error_message?: string;
};

// ─── Sortable header helper ───────────────────────────────────────────────────

function SortableHeader({
  label,
  columnId,
  sorting,
  onSort,
}: {
  label: string;
  columnId: string;
  sorting: SortingState;
  onSort: (id: string) => void;
}) {
  const current = sorting.find((s) => s.id === columnId);
  return (
    <button
      className="flex items-center gap-1 hover:text-foreground transition-colors"
      onClick={() => onSort(columnId)}
    >
      {label}
      {current ? (
        current.desc ? (
          <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronUp className="h-3.5 w-3.5" />
        )
      ) : (
        <ChevronsUpDown className="h-3.5 w-3.5 opacity-40" />
      )}
    </button>
  );
}

// ─── Props ────────────────────────────────────────────────────────────────────

interface ApplicationsTabProps {
  orgId: string;
  jobProfileId: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function ApplicationsTab({ orgId, jobProfileId }: ApplicationsTabProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Skill/trait filters from URL (multi-select, set by Analytics tab or filter panel)
  const skillFilters = searchParams.getAll("skill");
  const traitFilters = searchParams.getAll("trait");

  // Available skills/traits for filter badges
  const [availableSkills, setAvailableSkills] = useState<string[]>([]);
  const [availableTraits, setAvailableTraits] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    getJobProfileAnalytics(orgId, jobProfileId)
      .then((analytics) => {
        setAvailableSkills(analytics.top_skills.map((s) => s.skill));
        setAvailableTraits(analytics.top_traits.map((t) => t.trait));
      })
      .catch(() => {
        // silently ignore — filters just won't have options
      });
  }, [orgId, jobProfileId]);

  // Server state
  const [data, setData] = useState<PaginatedApplications | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [retryingIds, setRetryingIds] = useState<Set<string>>(new Set());
  const [deletingAppIds, setDeletingAppIds] = useState<Set<string>>(new Set());

  // Table state (all server-side)
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0, // 0-based for TanStack, converted to 1-based for API
    pageSize: 10,
  });
  const [sorting, setSorting] = useState<SortingState>([
    { id: "submitted_at", desc: true },
  ]);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchInput, setSearchInput] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedSearch(searchInput);
      setPagination((p) => ({ ...p, pageIndex: 0 })); // reset to page 1
    }, 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  const skillFiltersKey = skillFilters.join(",");
  const traitFiltersKey = traitFilters.join(",");

  // Reset page when filter/status/skill/trait changes
  useEffect(() => {
    setPagination((p) => ({ ...p, pageIndex: 0 }));
  }, [statusFilter, skillFiltersKey, traitFiltersKey]);

  // Derived: convert TanStack sorting to API ordering string
  const ordering = useMemo(() => {
    if (sorting.length === 0) return "-submitted_at";
    const s = sorting[0];
    return `${s.desc ? "-" : ""}${s.id}`;
  }, [sorting]);

  // Fetch
  const fetchData = useCallback(async () => {
    const skills = skillFiltersKey ? skillFiltersKey.split(",") : [];
    const traits = traitFiltersKey ? traitFiltersKey.split(",") : [];
    try {
      const result = await listJobApplications(orgId, jobProfileId, {
        page: pagination.pageIndex + 1,
        page_size: pagination.pageSize,
        search: debouncedSearch || undefined,
        status: statusFilter || undefined,
        ordering,
        skill: skills.length > 0 ? skills : undefined,
        trait: traits.length > 0 ? traits : undefined,
      });
      setData(result);
    } catch (error) {
      if (error instanceof AxiosError && error.response?.status === 403) {
        toast.error("You don't have permission to view applications");
      } else {
        toast.error("Failed to load applications");
      }
    } finally {
      setIsLoading(false);
    }
  }, [
    orgId,
    jobProfileId,
    pagination,
    debouncedSearch,
    statusFilter,
    ordering,
    skillFiltersKey,
    traitFiltersKey,
  ]);

  useEffect(() => {
    setIsLoading(true);
    fetchData();
  }, [fetchData]);

  // Poll every 5s while any analysis is processing
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    const hasProcessing = data?.results.some((app) => {
      const a = (app.analysis ?? null) as unknown as AnalysisData | null;
      return a?.status && !["done", "failed"].includes(a.status);
    });
    if (hasProcessing) {
      if (!pollRef.current) {
        pollRef.current = setInterval(fetchData, 5000);
      }
    } else {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [data, fetchData]);

  // Handle retry
  const handleRetry = useCallback(
    async (e: React.MouseEvent, applicationId: string) => {
      e.stopPropagation();
      setRetryingIds((prev) => new Set(prev).add(applicationId));
      try {
        await retryAnalysis(applicationId);
        toast.success("Analysis re-triggered");
        setData((prev) =>
          prev
            ? {
                ...prev,
                results: prev.results.map((app) =>
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
              }
            : prev,
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
    },
    [],
  );

  // Delete application
  const handleDelete = useCallback(
    async (e: React.MouseEvent, applicationId: string) => {
      e.stopPropagation();
      setDeletingAppIds((prev) => new Set(prev).add(applicationId));
      try {
        await deleteJobApplication(orgId, jobProfileId, applicationId);
        toast.success("Application deleted");
        setData((prev) =>
          prev
            ? {
                ...prev,
                count: prev.count - 1,
                results: prev.results.filter((app) => app.id !== applicationId),
              }
            : prev,
        );
      } catch {
        toast.error("Failed to delete application");
      } finally {
        setDeletingAppIds((prev) => {
          const next = new Set(prev);
          next.delete(applicationId);
          return next;
        });
      }
    },
    [orgId, jobProfileId],
  );

  // Toggle sort for a column
  const handleSort = useCallback((id: string) => {
    setSorting((prev) => {
      const existing = prev.find((s) => s.id === id);
      if (!existing) return [{ id, desc: false }];
      if (!existing.desc) return [{ id, desc: true }];
      return [{ id: "submitted_at", desc: true }]; // reset
    });
    setPagination((p) => ({ ...p, pageIndex: 0 }));
  }, []);

  // ─── Column definitions ─────────────────────────────────────────────────
  const columns = useMemo<ColumnDef<JobApplicationDetailWithAnalysis>[]>(
    () => [
      {
        id: "applicant",
        header: () => (
          <SortableHeader
            label="Applicant"
            columnId="first_name"
            sorting={sorting}
            onSort={handleSort}
          />
        ),
        cell: ({ row }) => (
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 shrink-0">
              <User className="h-4 w-4 text-primary" />
            </div>
            <p className="font-medium text-sm">
              {row.original.first_name} {row.original.last_name}
            </p>
          </div>
        ),
      },
      {
        id: "contact",
        header: "Contact",
        cell: ({ row }) => (
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <Mail className="h-3.5 w-3.5 shrink-0" />
              {row.original.email}
            </div>
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <Phone className="h-3.5 w-3.5 shrink-0" />
              {row.original.phone}
            </div>
          </div>
        ),
      },
      {
        id: "status",
        header: () => (
          <SortableHeader
            label="Status"
            columnId="status"
            sorting={sorting}
            onSort={handleSort}
          />
        ),
        cell: ({ row }) => {
          const cfg = STATUS_CONFIG[row.original.status ?? "to_be_reviewed"];
          return (
            <Badge
              variant={cfg?.variant ?? "secondary"}
              className={cfg?.className}
            >
              {cfg?.label ?? row.original.status}
            </Badge>
          );
        },
      },
      {
        id: "ai_analysis",
        header: "AI Analysis",
        cell: ({ row }) => {
          const analysis = (row.original.analysis ??
            null) as unknown as AnalysisData | null;
          const analysisStatus = analysis?.status;
          const cfg = analysisStatus
            ? ANALYSIS_STATUS_CONFIG[analysisStatus]
            : null;
          const isProcessing =
            analysisStatus === "ocr_pending" || analysisStatus === "ai_pending";
          const appId = row.original.id ?? "";

          if (!cfg)
            return <span className="text-xs text-muted-foreground">—</span>;

          return (
            <div className="flex items-center gap-1.5">
              {isProcessing ? (
                <Loader2
                  className={`h-3.5 w-3.5 animate-spin ${cfg.className}`}
                />
              ) : (
                <cfg.icon className={`h-3.5 w-3.5 ${cfg.className}`} />
              )}
              <span className={`text-xs font-medium ${cfg.className}`}>
                {cfg.label}
              </span>
              {/* Retry button: for failed or stuck */}
              {(analysisStatus === "failed" ||
                (analysisStatus &&
                  !["done", "failed"].includes(analysisStatus))) && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-1.5 text-xs text-muted-foreground"
                  title={
                    analysisStatus === "failed" ? "Retry" : "Retry (stuck?)"
                  }
                  disabled={retryingIds.has(appId)}
                  onClick={(e) => handleRetry(e, appId)}
                >
                  {retryingIds.has(appId) ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <RefreshCw className="h-3 w-3" />
                  )}
                </Button>
              )}
            </div>
          );
        },
      },
      {
        id: "score",
        header: () => (
          <SortableHeader
            label="Category"
            columnId="score"
            sorting={sorting}
            onSort={handleSort}
          />
        ),
        cell: ({ row }) => {
          const analysis = (row.original.analysis ??
            null) as unknown as AnalysisData | null;
          if (analysis?.status !== "done" || !analysis?.score_category)
            return <span className="text-xs text-muted-foreground">—</span>;
          const cat = analysis.score_category;
          const colorMap: Record<string, string> = {
            suitable: "bg-emerald-100 text-emerald-800",
            potentially_suitable: "bg-amber-100 text-amber-800",
            unsuitable: "bg-red-100 text-red-800",
          };
          return (
            <Badge
              variant="secondary"
              className={`text-xs font-semibold ${colorMap[cat.key] ?? ""}`}
            >
              {cat.label}
            </Badge>
          );
        },
      },
      {
        id: "submitted_at",
        header: () => (
          <SortableHeader
            label="Submitted"
            columnId="submitted_at"
            sorting={sorting}
            onSort={handleSort}
          />
        ),
        cell: ({ row }) =>
          row.original.submitted_at ? (
            <span className="text-sm text-muted-foreground">
              {new Date(row.original.submitted_at).toLocaleDateString(
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
          ),
      },
      {
        id: "actions",
        header: () => null,
        cell: ({ row }) => {
          const appId = row.original.id ?? "";
          const isDeleting = deletingAppIds.has(appId);
          return (
            <div className="flex justify-end" onClick={(e) => e.stopPropagation()}>
              <AlertDialog>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground"
                      disabled={isDeleting}
                    >
                      {isDeleting ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <MoreHorizontal className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <AlertDialogTrigger asChild>
                      <DropdownMenuItem
                        className="text-destructive focus:text-destructive focus:bg-destructive/10"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete application
                      </DropdownMenuItem>
                    </AlertDialogTrigger>
                  </DropdownMenuContent>
                </DropdownMenu>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete application?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Delete the application from{" "}
                      <strong>
                        {row.original.first_name} {row.original.last_name}
                      </strong>
                      ? This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      onClick={(e) => handleDelete(e, appId)}
                    >
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          );
        },
      },
    ],
    [sorting, retryingIds, deletingAppIds, handleSort, handleRetry, handleDelete],
  );

  // ─── Table instance ─────────────────────────────────────────────────────
  const table = useReactTable({
    data: data?.results ?? [],
    columns,
    pageCount: data?.num_pages ?? -1,
    state: { pagination, sorting },
    onPaginationChange: setPagination,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
    manualFiltering: true,
  });

  // ─── Loading skeleton ───────────────────────────────────────────────────
  if (isLoading && !data) {
    return (
      <div className="space-y-3">
        <div className="flex gap-2">
          <Skeleton className="h-9 w-60" />
          <Skeleton className="h-9 w-36" />
        </div>
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-14 w-full" />
        <Skeleton className="h-14 w-full" />
        <Skeleton className="h-14 w-full" />
      </div>
    );
  }

  const isEmpty =
    !isLoading &&
    (data?.count ?? 0) === 0 &&
    !debouncedSearch &&
    !statusFilter &&
    skillFilters.length === 0 &&
    traitFilters.length === 0;

  if (isEmpty) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-16 text-center">
          <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <FileText className="h-7 w-7 text-primary" />
          </div>
          <h3 className="text-base font-semibold mb-1">No applications yet</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            Applications will appear here once candidates apply for this job
            profile.
          </p>
        </CardContent>
      </Card>
    );
  }

  const totalCount = data?.count ?? 0;
  const currentPage = pagination.pageIndex + 1;
  const numPages = data?.num_pages ?? 1;
  const pageSize = pagination.pageSize;
  const startRow = (currentPage - 1) * pageSize + 1;
  const endRow = Math.min(currentPage * pageSize, totalCount);

  const toggleSkill = (skill: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("skill");
    const next = skillFilters.includes(skill)
      ? skillFilters.filter((s) => s !== skill)
      : [...skillFilters, skill];
    next.forEach((s) => params.append("skill", s));
    router.replace(`?${params.toString()}`);
  };

  const toggleTrait = (trait: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("trait");
    const next = traitFilters.includes(trait)
      ? traitFilters.filter((t) => t !== trait)
      : [...traitFilters, trait];
    next.forEach((t) => params.append("trait", t));
    router.replace(`?${params.toString()}`);
  };

  const clearAllFilters = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("skill");
    params.delete("trait");
    router.replace(`?${params.toString()}`);
  };

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <Input
          placeholder="Search by name or email…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="h-9 w-64"
        />
        <Select
          value={statusFilter || "__all__"}
          onValueChange={(val) => setStatusFilter(val === "__all__" ? "" : val)}
        >
          <SelectTrigger className="h-9 w-44">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map((opt) => (
              <SelectItem
                key={opt.value || "__all__"}
                value={opt.value || "__all__"}
              >
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {(availableSkills.length > 0 || availableTraits.length > 0) && (
          <Button
            variant="outline"
            size="sm"
            className="h-9 gap-1.5"
            onClick={() => setShowFilters((v) => !v)}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            Filters
            {(skillFilters.length > 0 || traitFilters.length > 0) && (
              <span className="ml-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-semibold text-primary-foreground">
                {skillFilters.length + traitFilters.length}
              </span>
            )}
            {showFilters ? (
              <ChevronUp className="h-3.5 w-3.5 opacity-60" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5 opacity-60" />
            )}
          </Button>
        )}
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Rows per page</span>
          <Select
            value={String(pagination.pageSize)}
            onValueChange={(val) =>
              setPagination({ pageIndex: 0, pageSize: Number(val) })
            }
          >
            <SelectTrigger className="h-9 w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[10, 20, 50].map((n) => (
                <SelectItem key={n} value={String(n)}>
                  {n}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Collapsible skill/trait filter panel */}
      {showFilters && (
        <div className="rounded-lg border border-border/60 bg-muted/20 p-4 space-y-4">
          {(skillFilters.length > 0 || traitFilters.length > 0) && (
            <div className="flex justify-start">
              <Button onClick={clearAllFilters} variant={"ghost"}>
                Clear all
              </Button>
            </div>
          )}
          {availableSkills.length > 0 && (
            <div className="space-y-2">
              <p className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                <Sparkles className="h-3.5 w-3.5" />
                Skills
              </p>
              <div className="flex flex-wrap gap-2">
                {availableSkills.map((skill) => (
                  <Badge
                    key={skill}
                    variant={
                      skillFilters.includes(skill) ? "default" : "secondary"
                    }
                    className={`cursor-pointer text-xs transition-colors ${
                      skillFilters.includes(skill)
                        ? "bg-primary text-primary-foreground hover:bg-primary/90"
                        : "hover:bg-primary hover:text-primary-foreground"
                    }`}
                    onClick={() => toggleSkill(skill)}
                  >
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {availableTraits.length > 0 && (
            <div className="space-y-2">
              <p className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                <Star className="h-3.5 w-3.5" />
                Notable Traits
              </p>
              <div className="flex flex-wrap gap-2">
                {availableTraits.map((trait) => (
                  <Badge
                    key={trait}
                    variant={
                      traitFilters.includes(trait) ? "default" : "outline"
                    }
                    className={`cursor-pointer text-xs transition-colors ${
                      traitFilters.includes(trait)
                        ? "bg-primary text-primary-foreground border-primary hover:bg-primary/90"
                        : "hover:bg-primary hover:text-primary-foreground hover:border-primary"
                    }`}
                    onClick={() => toggleTrait(trait)}
                  >
                    {trait}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Table */}
      <div className="rounded-lg border border-border overflow-hidden shadow-sm">
        <Table>
          <TableHeader className="bg-muted/40">
            {table.getHeaderGroups().map((hg) => (
              <TableRow
                key={hg.id}
                className="border-b border-border/60 hover:bg-transparent"
              >
                {hg.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    className="text-xs font-semibold text-muted-foreground uppercase tracking-wide"
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: pageSize }).map((_, i) => (
                <TableRow key={i}>
                  {columns.map((_, ci) => (
                    <TableCell key={ci}>
                      <Skeleton className="h-5 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : table.getRowModel().rows.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center text-sm text-muted-foreground"
                >
                  No applications match your filters.
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((row) => {
                const appId = row.original.id ?? "";
                const href = `/job-profiles/${jobProfileId}/applications/${appId}`;
                return (
                  <TableRow
                    key={row.id}
                    className="cursor-pointer hover:bg-primary/4 transition-colors"
                    onClick={(e) => {
                      if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        window.open(href, "_blank");
                      } else {
                        router.push(href);
                      }
                    }}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination controls */}
      <div className="flex items-center justify-between text-sm">
        <p className="text-muted-foreground">
          {totalCount > 0
            ? `Showing ${startRow}–${endRow} of ${totalCount} result${totalCount !== 1 ? "s" : ""}`
            : "No results"}
        </p>
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => setPagination((p) => ({ ...p, pageIndex: 0 }))}
            disabled={currentPage === 1}
          >
            <ChevronsLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() =>
              setPagination((p) => ({ ...p, pageIndex: p.pageIndex - 1 }))
            }
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="px-2 text-muted-foreground">
            Page {currentPage} of {numPages}
          </span>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() =>
              setPagination((p) => ({ ...p, pageIndex: p.pageIndex + 1 }))
            }
            disabled={currentPage >= numPages}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() =>
              setPagination((p) => ({ ...p, pageIndex: numPages - 1 }))
            }
            disabled={currentPage >= numPages}
          >
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
