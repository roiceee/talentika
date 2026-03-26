"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import { useAuth } from "@/contexts/auth-context";
import { getOrgAnalytics, type OrgAnalytics } from "@/lib/api";
import { EMPLOYMENT_TYPE_LABELS } from "@/lib/constants/job-profile";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  StatusBreakdownChart,
  CategoryDistributionChart,
  ApplicationsOverTimeChart,
  JobProfileBarChart,
  DoughnutChart,
  SCORE_CATEGORY_COLORS,
} from "@/components/analytics-charts";
import {
  Users,
  Briefcase,
  Brain,
  TrendingUp,
  Sparkles,
  Star,
  BarChart3,
  Building2,
} from "lucide-react";

// ─── Component ────────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<OrgAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const orgId = user?.default_organization;

  const fetchAnalytics = useCallback(async () => {
    if (!orgId) return;
    try {
      const result = await getOrgAnalytics(orgId);
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
  }, [orgId]);

  useEffect(() => {
    if (!orgId) {
      router.replace("/organizations");
      return;
    }
    fetchAnalytics();
  }, [orgId, fetchAnalytics, router]);

  // ─── Loading ──────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="mx-auto w-full max-w-300 px-6 py-8 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-64 rounded-lg" />
          <Skeleton className="h-64 rounded-lg" />
        </div>
        <Skeleton className="h-64 rounded-lg" />
      </div>
    );
  }

  if (!data) return null;

  const totalApps = data.total_applications;
  const statusBreakdown = data.status_breakdown;

  return (
    <div className="mx-auto w-full max-w-300 px-6 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Organization Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Aggregated insights across all job profiles
        </p>
      </div>

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
              Job Profiles
            </CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {data.total_job_profiles.total}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {data.total_job_profiles.active} active ·{" "}
              {data.total_job_profiles.inactive} inactive
            </p>
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
                className={`text-3xl font-bold ${SCORE_CATEGORY_COLORS[data.average_category.key] ?? ""}`}
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
              Score Distribution
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
            <ApplicationsOverTimeChart data={data.applications_over_time} />
          </CardContent>
        </Card>
      )}

      {/* ─── Per-Job-Profile Breakdown ────────────────────────────── */}
      {data.applications_by_job_profile.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Building2 className="h-4 w-4" />
              Applications by Job Profile
            </CardTitle>
          </CardHeader>
          <CardContent>
            <JobProfileBarChart
              labels={data.applications_by_job_profile.map((p) => p.title)}
              data={data.applications_by_job_profile.map(
                (p) => p.application_count,
              )}
              height={Math.max(
                160,
                data.applications_by_job_profile.length * 36,
              )}
            />
          </CardContent>
        </Card>
      )}

      {/* ─── Employment Type Breakdown ────────────────────────────── */}
      {Object.keys(data.employment_type_breakdown).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Briefcase className="h-4 w-4" />
              Applications by Employment Type
            </CardTitle>
          </CardHeader>
          <CardContent className="flex justify-center">
            <DoughnutChart
              labels={Object.keys(data.employment_type_breakdown).map(
                (t) => EMPLOYMENT_TYPE_LABELS[t] ?? t,
              )}
              data={Object.values(data.employment_type_breakdown)}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
