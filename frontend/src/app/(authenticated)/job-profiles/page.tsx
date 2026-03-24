"use client";

import { useEffect, useState, useCallback } from "react";
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
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Briefcase, Plus, Clock } from "lucide-react";

export default function JobProfilesPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [jobProfiles, setJobProfiles] = useState<JobProfileList[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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
      // No default org — send to organizations page to pick one
      router.replace("/organizations");
      return;
    }
    fetchData();
  }, [orgId, fetchData, router]);

  const employmentTypeLabels: Record<string, string> = {
    full_time: "Full Time",
    part_time: "Part Time",
    contract: "Contract",
    internship: "Internship",
    freelance: "Freelance",
    not_applicable: "N/A",
  };

  if (!orgId || isLoading) {
    return (
      <div className="w-full py-8 space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-9 w-36" />
        </div>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full py-8">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="font-heading text-2xl">Job Profiles</h1>
          <p className="text-muted-foreground text-sm mt-0.5">
            Manage your organization&apos;s job profiles
          </p>
        </div>
        <Button onClick={() => router.push("/job-profiles/create")} className="gap-2">
          <Plus className="h-4 w-4" />
          New job profile
        </Button>
      </div>

      {jobProfiles.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <Briefcase className="h-7 w-7 text-primary" />
            </div>
            <h3 className="mb-1 font-heading text-lg">No job profiles yet</h3>
            <p className="mb-6 text-sm text-muted-foreground text-center max-w-sm">
              Create your first job profile to start receiving and managing applications.
            </p>
            <Button onClick={() => router.push("/job-profiles/create")} className="gap-2">
              <Plus className="h-4 w-4" />
              Create job profile
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {jobProfiles.map((profile) => (
            <Link
              key={profile.id}
              href={`/job-profiles/${profile.id}`}
              className="block group"
            >
              <Card className="transition-all duration-150 hover:shadow-md hover:border-primary/25 border-l-4 border-l-transparent hover:border-l-primary">
                <CardHeader className="py-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <CardTitle className="text-base group-hover:text-primary transition-colors truncate">
                        {profile.title}
                      </CardTitle>
                      {profile.category_name && (
                        <p className="text-xs text-muted-foreground mt-0.5">{profile.category_name}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {profile.employment_type && profile.employment_type !== "not_applicable" && (
                        <Badge variant="secondary" className="text-xs font-normal">
                          {employmentTypeLabels[profile.employment_type] ?? profile.employment_type}
                        </Badge>
                      )}
                      {profile.experience_level_name && (
                        <Badge variant="outline" className="text-xs font-normal">
                          {profile.experience_level_name}
                        </Badge>
                      )}
                    </div>
                  </div>
                  {profile.created_at && (
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1">
                      <Clock className="h-3 w-3" />
                      <span>Created {new Date(profile.created_at).toLocaleDateString()}</span>
                    </div>
                  )}
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
