"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import { useAuth } from "@/contexts/auth-context";
import type { JobProfileList } from "@/lib/client";
import { listJobProfiles } from "@/lib/api";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Briefcase, Plus, Clock, ArrowUpDown, Search, X, Users } from "lucide-react";

const STATUS_DISPLAY: Record<string, { label: string; className: string }> = {
  to_be_reviewed: { label: "To Review",   className: "text-muted-foreground" },
  reviewed:       { label: "Reviewed",    className: "text-blue-600" },
  shortlisted:    { label: "Shortlisted", className: "text-green-600" },
  rejected:       { label: "Rejected",    className: "text-red-500" },
};

const EMPLOYMENT_TYPE_LABELS: Record<string, string> = {
  full_time: "Full Time",
  part_time: "Part Time",
  contract: "Contract",
  internship: "Internship",
  freelance: "Freelance",
  not_applicable: "N/A",
};

export default function JobProfilesPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [jobProfiles, setJobProfiles] = useState<JobProfileList[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [filterEmployment, setFilterEmployment] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [sort, setSort] = useState("newest");

  const orgId = user?.default_organization;

  const fetchData = useCallback(async () => {
    if (!orgId) return;
    try {
      const profiles = await listJobProfiles(orgId);
      setJobProfiles(profiles ?? []);
    } catch (error) {
      if (error instanceof AxiosError) {
        if (error.response?.status === 403 || error.response?.status === 404) {
          toast.error("Organization not found or you don't have access");
          router.push("/organizations");
          return;
        }
      }
      toast.error("Failed to load job profiles");
    } finally {
      setIsLoading(false);
    }
  }, [orgId, router]);

  useEffect(() => {
    if (!orgId) {
      router.replace("/organizations");
      return;
    }
    fetchData();
  }, [orgId, fetchData, router]);

  const filtered = useMemo(() => {
    let result = [...jobProfiles];

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.category_name?.toLowerCase().includes(q) ||
          p.experience_level_name?.toLowerCase().includes(q),
      );
    }

    if (filterEmployment !== "all") {
      result = result.filter((p) => p.employment_type === filterEmployment);
    }

    if (filterStatus === "active") {
      result = result.filter((p) => p.is_active === true);
    } else if (filterStatus === "inactive") {
      result = result.filter((p) => p.is_active === false);
    }

    result.sort((a, b) => {
      if (sort === "newest")
        return (
          new Date(b.created_at ?? 0).getTime() -
          new Date(a.created_at ?? 0).getTime()
        );
      if (sort === "oldest")
        return (
          new Date(a.created_at ?? 0).getTime() -
          new Date(b.created_at ?? 0).getTime()
        );
      if (sort === "az") return a.title.localeCompare(b.title);
      if (sort === "za") return b.title.localeCompare(a.title);
      return 0;
    });

    return result;
  }, [jobProfiles, search, filterEmployment, filterStatus, sort]);

  const hasFilters =
    search.trim() || filterEmployment !== "all" || filterStatus !== "all";

  function clearFilters() {
    setSearch("");
    setFilterEmployment("all");
    setFilterStatus("all");
  }

  if (!orgId || isLoading) {
    return (
      <div className="w-full py-8 space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-9 w-36" />
        </div>
        <div className="flex gap-3">
          <Skeleton className="h-9 flex-1" />
          <Skeleton className="h-9 w-40" />
          <Skeleton className="h-9 w-36" />
          <Skeleton className="h-9 w-36" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-44 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-2xl">Job Profiles</h1>
          <p className="text-muted-foreground text-sm mt-0.5">
            Manage your organization&apos;s job profiles
          </p>
        </div>
        <Button
          onClick={() => router.push("/job-profiles/create")}
          className="gap-2"
        >
          <Plus className="h-4 w-4" />
          New job profile
        </Button>
      </div>

      {jobProfiles.length > 0 && (
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
            <Input
              placeholder="Search by title, category, level…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
            />
          </div>

          <Select value={filterEmployment} onValueChange={setFilterEmployment}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Employment type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {Object.entries(EMPLOYMENT_TYPE_LABELS)
                .filter(([k]) => k !== "not_applicable")
                .map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>

          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
            </SelectContent>
          </Select>

          <Select value={sort} onValueChange={setSort}>
            <SelectTrigger className="w-40">
              <ArrowUpDown className="h-3.5 w-3.5 mr-1.5 text-muted-foreground" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest first</SelectItem>
              <SelectItem value="oldest">Oldest first</SelectItem>
              <SelectItem value="az">Title A–Z</SelectItem>
              <SelectItem value="za">Title Z–A</SelectItem>
            </SelectContent>
          </Select>

          {hasFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFilters}
              className="gap-1.5 text-muted-foreground"
            >
              <X className="h-3.5 w-3.5" />
              Clear
            </Button>
          )}
        </div>
      )}

      {jobProfiles.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <Briefcase className="h-7 w-7 text-primary" />
            </div>
            <h3 className="mb-1 font-heading text-lg">No job profiles yet</h3>
            <p className="mb-6 text-sm text-muted-foreground text-center max-w-sm">
              Create your first job profile to start receiving and managing
              applications.
            </p>
            <Button
              onClick={() => router.push("/job-profiles/create")}
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              Create job profile
            </Button>
          </CardContent>
        </Card>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Search className="h-10 w-10 text-muted-foreground/40 mb-3" />
          <p className="font-medium">No profiles match your filters</p>
          <p className="text-sm text-muted-foreground mt-1">
            Try adjusting your search or filters.
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={clearFilters}
            className="mt-4"
          >
            Clear filters
          </Button>
        </div>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">
            {filtered.length} of {jobProfiles.length} profile
            {jobProfiles.length !== 1 ? "s" : ""}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((profile) => (
              <Link
                key={profile.id}
                href={`/job-profiles/${profile.id}`}
                className="block group"
              >
                <Card className="h-full flex flex-col transition-all duration-150 hover:shadow-md hover:border-primary/30">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <CardTitle className="text-base leading-snug group-hover:text-primary transition-colors line-clamp-2">
                          {profile.title}
                        </CardTitle>
                        {profile.category_name && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {profile.category_name}
                          </p>
                        )}
                      </div>
                      <Badge
                        variant={profile.is_active ? "default" : "secondary"}
                        className="shrink-0 text-xs font-normal"
                      >
                        {profile.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                  </CardHeader>

                  <CardContent className="flex-1 pb-3 space-y-3">
                    <div className="flex flex-wrap gap-1.5">
                      {profile.employment_type &&
                        profile.employment_type !== "not_applicable" && (
                          <Badge
                            variant="secondary"
                            className="text-xs font-normal"
                          >
                            {EMPLOYMENT_TYPE_LABELS[profile.employment_type] ??
                              profile.employment_type}
                          </Badge>
                        )}
                      {profile.experience_level_name && (
                        <Badge
                          variant="outline"
                          className="text-xs font-normal"
                        >
                          {profile.experience_level_name}
                        </Badge>
                      )}
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Users className="h-3.5 w-3.5" />
                        <span>
                          {profile.application_count ?? 0} applicant
                          {(profile.application_count ?? 0) !== 1 ? "s" : ""}
                        </span>
                      </div>
                      {profile.application_status_counts &&
                        (profile.application_count ?? 0) > 0 && (
                          <div className="flex flex-wrap gap-x-2 gap-y-0.5 text-xs pl-5">
                            {Object.entries(STATUS_DISPLAY).map(([key, { label, className }]) => {
                              const count = profile.application_status_counts?.[key] ?? 0;
                              if (count === 0) return null;
                              return (
                                <span key={key} className={className}>
                                  {count} {label}
                                </span>
                              );
                            })}
                          </div>
                        )}
                    </div>
                  </CardContent>

                  <CardFooter className="pt-0 pb-4">
                    {profile.created_at && (
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        <span>
                          {new Date(profile.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </CardFooter>
                </Card>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
