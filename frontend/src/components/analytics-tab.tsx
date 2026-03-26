"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import { getJobProfileAnalytics, type JobProfileAnalytics } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  StatusBreakdownChart,
  CategoryDistributionChart,
  ApplicationsOverTimeChart,
} from "@/components/analytics-charts";
import {
  Users,
  BarChart3,
  Brain,
  TrendingUp,
  Sparkles,
  Star,
} from "lucide-react";

// ─── Props ────────────────────────────────────────────────────────────────────

interface AnalyticsTabProps {
  orgId: string;
  jobProfileId: string;
  /** Base path for the job profile page (e.g. /job-profiles/[id]) */
  basePath: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

export function AnalyticsTab({ orgId, jobProfileId, basePath }: AnalyticsTabProps) {
  const router = useRouter();
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

  return (
    <div className="space-y-6">
      {/* ─── KPI Cards ──────────────────────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-l-4 border-l-primary">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Applications
            </CardTitle>
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
              <Users className="h-4 w-4 text-primary" />
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-primary">{totalApps}</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Average Category
            </CardTitle>
            <div className="h-8 w-8 rounded-full bg-blue-50 flex items-center justify-center">
              <Brain className="h-4 w-4 text-blue-500" />
            </div>
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

        <Card className="border-l-4 border-l-emerald-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Shortlisted
            </CardTitle>
            <div className="h-8 w-8 rounded-full bg-emerald-50 flex items-center justify-center">
              <Star className="h-4 w-4 text-emerald-600" />
            </div>
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

        <Card className="border-l-4 border-l-destructive">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Rejected
            </CardTitle>
            <div className="h-8 w-8 rounded-full bg-destructive/10 flex items-center justify-center">
              <TrendingUp className="h-4 w-4 text-destructive" />
            </div>
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
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-4 w-4" />
              Status Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            {totalApps === 0 ? (
              <p className="text-sm text-muted-foreground">No data yet</p>
            ) : (
              <StatusBreakdownChart statusBreakdown={statusBreakdown} />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Brain className="h-4 w-4" />
              Category Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CategoryDistributionChart
              categoryDistribution={data.category_distribution}
            />
          </CardContent>
        </Card>
      </div>

      {/* ─── Top Skills + Top Traits ──────────────────────────────── */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4" />
              Top Skills
              <Badge variant="secondary" className="text-xs font-normal">
                {data.top_skills.length}
              </Badge>
            </CardTitle>
            {data.top_skills.length > 0 && (
              <p className="text-xs text-muted-foreground">
                Click a skill to filter applications
              </p>
            )}
          </CardHeader>
          <CardContent>
            {data.top_skills.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No skill data available yet
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {data.top_skills.map((s, i) => (
                  <Badge
                    key={i}
                    variant="secondary"
                    className="text-xs gap-1 cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
                    onClick={() =>
                      router.push(
                        `${basePath}?tab=applications&skill=${encodeURIComponent(s.skill)}`,
                      )
                    }
                  >
                    {s.skill}
                    <span className="opacity-60">({s.count})</span>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Star className="h-4 w-4" />
              Notable Traits
              <Badge variant="secondary" className="text-xs font-normal">
                {data.top_traits.length}
              </Badge>
            </CardTitle>
            {data.top_traits.length > 0 && (
              <p className="text-xs text-muted-foreground">
                Click a trait to filter applications
              </p>
            )}
          </CardHeader>
          <CardContent>
            {data.top_traits.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No trait data available yet
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {data.top_traits.map((t, i) => (
                  <Badge
                    key={i}
                    variant="outline"
                    className="text-xs gap-1 cursor-pointer hover:bg-primary hover:text-primary-foreground hover:border-primary transition-colors"
                    onClick={() =>
                      router.push(
                        `${basePath}?tab=applications&trait=${encodeURIComponent(t.trait)}`,
                      )
                    }
                  >
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
            <ApplicationsOverTimeChart data={data.applications_over_time} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
