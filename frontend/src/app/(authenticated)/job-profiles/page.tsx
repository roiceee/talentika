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
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Briefcase, Plus } from "lucide-react";

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
      <div className="mx-auto w-full max-w-4xl px-6 py-8 space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-8">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-heading text-2xl font-semibold">
              Job Profiles
            </h1>
            <p className="text-muted-foreground">
              Manage your organization&apos;s job profiles
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={() => router.push("/job-profiles/create")}>
              <Plus className="mr-2 h-4 w-4" />
              New job profile
            </Button>
          </div>
        </div>
      </div>

      {jobProfiles.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Briefcase className="mb-4 h-12 w-12 text-muted-foreground" />
            <h3 className="mb-2 font-heading text-lg font-semibold">
              No job profiles yet
            </h3>
            <p className="mb-4 text-sm text-muted-foreground text-center max-w-md">
              Create your first job profile to start receiving and managing
              applications.
            </p>
            <Button onClick={() => router.push("/job-profiles/create")}>
              <Plus className="mr-2 h-4 w-4" />
              Create job profile
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {jobProfiles.map((profile) => (
            <Link
              key={profile.id}
              href={`/job-profiles/${profile.id}`}
              className="block"
            >
              <Card className="transition-colors hover:bg-muted/50">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{profile.title}</CardTitle>
                  </div>
                  {profile.category_name && (
                    <CardDescription>{profile.category_name}</CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    {profile.employment_type && (
                      <span>
                        {employmentTypeLabels[profile.employment_type] ??
                          profile.employment_type}
                      </span>
                    )}
                    {profile.experience_level_name && (
                      <span>{profile.experience_level_name}</span>
                    )}
                    {profile.created_at && (
                      <span>
                        Created{" "}
                        {new Date(profile.created_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
