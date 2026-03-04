"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { AxiosError } from "axios";
import { getJobProfileAnalytics, type JobProfileAnalytics } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Users,
  BarChart3,
  Brain,
  TrendingUp,
  Sparkles,
  Star,
} from "lucide-react";

// ─── Status config ───────────────────────────────────────────────────────────

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  to_be_reviewed: {
    label: "To Be Reviewed",
    color: "bg-gray-200 text-gray-800",
  },
  reviewed: { label: "Reviewed", color: "bg-blue-100 text-blue-800" },
  shortlisted: {
    label: "Shortlisted",
    color: "bg-emerald-100 text-emerald-800",
  },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-800" },
};

const CATEGORY_LABELS: Record<string, { label: string; color: string }> = {
  excellent: { label: "Excellent", color: "bg-emerald-600" },
  good: { label: "Good", color: "bg-blue-500" },
  moderate: { label: "Moderate", color: "bg-amber-500" },
  bad: { label: "Bad", color: "bg-red-500" },
};

// ─── Props ────────────────────────────────────────────────────────────────────

interface AnalyticsTabProps {
  orgId: string;
  jobProfileId: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function AnalyticsTab({ orgId, jobProfileId }: AnalyticsTabProps) {
  const [data, setData] = useState<JobProfileAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAnalytics = useCallback(async () => {
    try {
      const result = await getJobProfileAnalytics(orgId, jobProfileId);
      setData(result);
    } catch (error) {
      if (error instanceof AxiosError && error.response?.status === 403) {
        toast.error("You don't have permission to view analytics");
      } else {
        toast.error("Failed to load analytics");
      }
    } finally {
      setIsLoading(false);
    }
  }, [orgId, jobProfileId]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  // ─── Loading ────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-64 rounded-lg" />
          <Skeleton className="h-64 rounded-lg" />
        </div>
      </div>
    );
  }

  if (!data) return null;

  const totalApps = data.total_applications;
  const statusBreakdown = data.status_breakdown;
  const catDist = data.category_distribution;
  const maxCatBucket = Math.max(...Object.values(catDist), 1);

  return (
    <div className="space-y-6">
      {/* ─── KPI Cards ──────────────────────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Applications
            </CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{totalApps}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Average Category
            </CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {data.average_category ? (
              <p
                className={`text-3xl font-bold ${
                  {
                    excellent: "text-emerald-600",
                    good: "text-blue-600",
                    moderate: "text-amber-600",
                    bad: "text-destructive",
                  }[data.average_category.key] ?? ""
                }`}
              >
                {data.average_category.label}
              </p>
            ) : (
              <p className="text-3xl font-bold text-muted-foreground">—</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Shortlisted
            </CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-emerald-600">
              {statusBreakdown["shortlisted"] ?? 0}
            </p>
            {totalApps > 0 && (
              <p className="text-xs text-muted-foreground mt-1">
                {Math.round(
                  ((statusBreakdown["shortlisted"] ?? 0) / totalApps) * 100,
                )}
                % of total
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Rejected
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-destructive">
              {statusBreakdown["rejected"] ?? 0}
            </p>
            {totalApps > 0 && (
              <p className="text-xs text-muted-foreground mt-1">
                {Math.round(
                  ((statusBreakdown["rejected"] ?? 0) / totalApps) * 100,
                )}
                % of total
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ─── Status Breakdown + Score Distribution ─────────────────── */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Status Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-4 w-4" />
              Status Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            {Object.keys(statusBreakdown).length === 0 ? (
              <p className="text-sm text-muted-foreground">No data yet</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(STATUS_LABELS).map(([key, cfg]) => {
                  const count = statusBreakdown[key] ?? 0;
                  const pct = totalApps > 0 ? (count / totalApps) * 100 : 0;
                  return (
                    <div key={key} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{cfg.label}</span>
                        <span className="text-muted-foreground">
                          {count} ({Math.round(pct)}%)
                        </span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${cfg.color.split(" ")[0].replace("bg-", "bg-")}`}
                          style={{
                            width: `${pct}%`,
                            backgroundColor:
                              key === "to_be_reviewed"
                                ? "#9ca3af"
                                : key === "reviewed"
                                  ? "#3b82f6"
                                  : key === "shortlisted"
                                    ? "#059669"
                                    : "#ef4444",
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Category Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Brain className="h-4 w-4" />
              Category Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-end gap-3 h-40">
              {Object.entries(CATEGORY_LABELS).map(([key, cfg]) => {
                const count = catDist[key] ?? 0;
                return (
                  <div
                    key={key}
                    className="flex-1 flex flex-col items-center gap-1"
                  >
                    <span className="text-xs font-medium text-muted-foreground">
                      {count}
                    </span>
                    <div
                      className={`w-full rounded-t ${cfg.color} transition-all`}
                      style={{
                        height: `${(count / maxCatBucket) * 100}%`,
                        minHeight: count > 0 ? "4px" : "0px",
                      }}
                    />
                    <span className="text-[11px] font-medium text-muted-foreground mt-1">
                      {cfg.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ─── Top Skills + Top Traits ──────────────────────────────── */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Top Skills */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4" />
              Top Skills
              <Badge variant="secondary" className="text-xs font-normal">
                {data.top_skills.length}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.top_skills.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No skill data available yet
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {data.top_skills.map((s, i) => (
                  <Badge key={i} variant="secondary" className="text-xs gap-1">
                    {s.skill}
                    <span className="opacity-60">({s.count})</span>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Traits */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Star className="h-4 w-4" />
              Notable Traits
              <Badge variant="secondary" className="text-xs font-normal">
                {data.top_traits.length}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.top_traits.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No trait data available yet
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {data.top_traits.map((t, i) => (
                  <Badge key={i} variant="outline" className="text-xs gap-1">
                    {t.trait}
                    <span className="opacity-60">({t.count})</span>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ─── Applications Over Time ───────────────────────────────── */}
      {data.applications_over_time.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingUp className="h-4 w-4" />
              Applications Over Time
              <span className="text-xs font-normal text-muted-foreground">
                (last 30 days)
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(() => {
              const maxCount = Math.max(
                ...data.applications_over_time.map((d) => d.count),
                1,
              );
              return (
                <div className="flex items-end gap-1 h-32">
                  {data.applications_over_time.map((d, i) => (
                    <div
                      key={i}
                      className="flex-1 flex flex-col items-center gap-0.5 group relative"
                    >
                      <div
                        className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                        style={{
                          height: `${(d.count / maxCount) * 100}%`,
                          minHeight: d.count > 0 ? "4px" : "0px",
                        }}
                      />
                      {/* Tooltip on hover */}
                      <div className="absolute bottom-full mb-1 hidden group-hover:block bg-popover text-popover-foreground border rounded px-2 py-1 text-xs whitespace-nowrap shadow-sm z-10">
                        {new Date(d.date).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                        })}
                        : {d.count} application{d.count !== 1 ? "s" : ""}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })()}
            <div className="flex justify-between mt-2 text-[10px] text-muted-foreground">
              {data.applications_over_time.length > 0 && (
                <>
                  <span>
                    {new Date(
                      data.applications_over_time[0].date,
                    ).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                  <span>
                    {new Date(
                      data.applications_over_time[
                        data.applications_over_time.length - 1
                      ].date,
                    ).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
