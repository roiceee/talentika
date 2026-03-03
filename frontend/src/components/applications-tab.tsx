"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import {
  listJobApplications,
  retryAnalysis,
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
} from "lucide-react";

// ─── Config ──────────────────────────────────────────────────────────────────

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

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "to_be_reviewed", label: "To Be Reviewed" },
  { value: "reviewed", label: "Reviewed" },
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
  score?: number | null;
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

  // Server state
  const [data, setData] = useState<PaginatedApplications | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [retryingIds, setRetryingIds] = useState<Set<string>>(new Set());

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

  // Reset page when filter/status changes
  useEffect(() => {
    setPagination((p) => ({ ...p, pageIndex: 0 }));
  }, [statusFilter]);

  // Derived: convert TanStack sorting to API ordering string
  const ordering = useMemo(() => {
    if (sorting.length === 0) return "-submitted_at";
    const s = sorting[0];
    return `${s.desc ? "-" : ""}${s.id}`;
  }, [sorting]);

  // Fetch
  const fetchData = useCallback(async () => {
    try {
      const result = await listJobApplications(orgId, jobProfileId, {
        page: pagination.pageIndex + 1,
        page_size: pagination.pageSize,
        search: debouncedSearch || undefined,
        status: statusFilter || undefined,
        ordering,
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
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted shrink-0">
              <User className="h-4 w-4 text-muted-foreground" />
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
            label="Score"
            columnId="score"
            sorting={sorting}
            onSort={handleSort}
          />
        ),
        cell: ({ row }) => {
          const analysis = (row.original.analysis ??
            null) as unknown as AnalysisData | null;
          if (analysis?.status !== "done" || analysis?.score == null)
            return <span className="text-xs text-muted-foreground">—</span>;
          return (
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
    ],
    [sorting, retryingIds, handleSort, handleRetry],
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
    !isLoading && (data?.count ?? 0) === 0 && !debouncedSearch && !statusFilter;

  if (isEmpty) {
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

  const totalCount = data?.count ?? 0;
  const currentPage = pagination.pageIndex + 1;
  const numPages = data?.num_pages ?? 1;
  const pageSize = pagination.pageSize;
  const startRow = (currentPage - 1) * pageSize + 1;
  const endRow = Math.min(currentPage * pageSize, totalCount);

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

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((hg) => (
              <TableRow key={hg.id}>
                {hg.headers.map((header) => (
                  <TableHead key={header.id}>
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
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() =>
                    router.push(
                      `/job-profiles/${jobProfileId}/applications/${row.original.id}`,
                    )
                  }
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
              ))
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
