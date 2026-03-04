"use client";

import { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import {
  getJobProfile,
  updateJobProfile,
  listJobCategories,
  listExperienceLevels,
} from "@/lib/api";
import type {
  JobProfileDetail,
  JobCategory,
  ExperienceLevel,
  Qualification,
} from "@/lib/client";
import {
  JobProfileForm,
  type JobProfileFormValues,
} from "@/components/job-profile-form";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { ApplicationsTab } from "@/components/applications-tab";
import { ResultsTab } from "@/components/results-tab";
import { AnalyticsTab } from "@/components/analytics-tab";
import { QualificationsDisplay } from "@/components/qualifications-display";
import {
  EMPLOYMENT_TYPE_LABELS,
  QUESTION_TYPE_LABELS,
} from "@/lib/constants/job-profile";
import {
  ArrowLeft,
  Pencil,
  X,
  List,
  MessageSquare,
  LinkIcon,
  FileText,
  Star,
  BarChart3,
  Loader2,
  Lock,
} from "lucide-react";

export default function JobProfileDetailPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeTab = searchParams.get("tab") ?? "details";

  const [profile, setProfile] = useState<JobProfileDetail | null>(null);
  const [categories, setCategories] = useState<JobCategory[]>([]);
  const [experienceLevels, setExperienceLevels] = useState<ExperienceLevel[]>(
    [],
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isEditMode, setIsEditMode] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTogglingActive, setIsTogglingActive] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [prof, cats, levels] = await Promise.all([
        getJobProfile(jobId),
        listJobCategories(),
        listExperienceLevels(),
      ]);
      setProfile(prof);
      setCategories(cats ?? []);
      setExperienceLevels(levels ?? []);
    } catch (error) {
      if (error instanceof AxiosError) {
        if (error.response?.status === 403 || error.response?.status === 404) {
          toast.error("Job profile not found");
          router.push("/job-profiles");
          return;
        }
      }
      toast.error("Failed to load job profile");
    } finally {
      setIsLoading(false);
    }
  }, [jobId, router]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  async function handleUpdate(values: JobProfileFormValues) {
    setIsSubmitting(true);
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const payload: any = {
        title: values.title,
        category: values.category,
        employment_type: values.employment_type,
        experience_level: values.experience_level,
        description: values.description,
        qualifications: values.qualifications.map((q, i) => ({
          ...(q.id ? { id: q.id } : {}),
          category: q.category,
          name: q.name,
          requirement_level: q.requirement_level,
          years_required: q.years_required ?? null,
          proficiency_level: q.proficiency_level ?? null,
          order: i,
        })),
        is_active: values.is_active,
        questions: values.questions.map((q, i) => ({
          ...(q.id ? { id: q.id } : {}),
          text: q.text,
          question_type: q.question_type,
          order: i,
          choices: q.choices.filter((c) => c.trim()),
          is_required: q.is_required,
        })),
      };

      const updated = await updateJobProfile(jobId, payload);
      setProfile(updated);
      toast.success("Job profile updated");
      setIsEditMode(false);
    } catch (error) {
      if (error instanceof AxiosError) {
        const data = error.response?.data;
        if (typeof data === "object" && data !== null) {
          const messages = Object.entries(data)
            .map(
              ([key, val]) =>
                `${key}: ${Array.isArray(val) ? val.join(", ") : val}`,
            )
            .join("; ");
          toast.error(messages || "Failed to update job profile");
        } else {
          toast.error("Failed to update job profile");
        }
      } else {
        toast.error("Failed to update job profile");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleToggleActive() {
    if (!profile) return;
    setIsTogglingActive(true);
    try {
      const updated = await updateJobProfile(jobId, {
        is_active: !profile.is_active,
      });
      setProfile(updated);
      toast.success(
        updated.is_active
          ? "Now accepting applications"
          : "No longer accepting applications",
      );
    } catch {
      toast.error("Failed to update status");
    } finally {
      setIsTogglingActive(false);
    }
  }

  function buildInitialValues(p: JobProfileDetail): JobProfileFormValues {
    return {
      title: p.title ?? "",
      category: (p.category as { id?: string })?.id ?? "",
      employment_type:
        (p.employment_type as JobProfileFormValues["employment_type"]) ??
        "full_time",
      experience_level: (p.experience_level as { id?: string })?.id ?? "",
      description: p.description ?? "",
      qualifications: ((p.qualifications ?? []) as Qualification[]).map(
        (q) => ({
          id: q.id,
          category: q.category,
          name: q.name,
          requirement_level: q.requirement_level ?? "required",
          years_required: q.years_required ?? null,
          proficiency_level: q.proficiency_level ?? null,
          order: q.order ?? 0,
        }),
      ),
      is_active: p.is_active ?? true,
      questions: (p.questions ?? []).map((q) => ({
        id: q.id,
        text: q.text,
        question_type: q.question_type ?? "text",
        order: q.order ?? 0,
        choices: q.choices ?? [],
        is_required: q.is_required ?? true,
      })),
    };
  }

  // ─── Loading skeleton ────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="w-full py-8 space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-lg" />
        <Skeleton className="h-40 w-full rounded-lg" />
      </div>
    );
  }

  if (!profile) return null;

  const isActive = profile.is_active ?? true;
  const applicationCount = profile.application_count ?? 0;
  const hasSubmissions = applicationCount > 0;
  const qualifications = (profile.qualifications ?? []) as Qualification[];

  // ─── Edit mode ───────────────────────────────────────────────────────────
  if (isEditMode) {
    return (
      <div className="w-full py-8">
        <div className="mb-6">
          <Button
            variant={"ghost"}
            onClick={() => setIsEditMode(false)}
            className="inline-flex items-center gap-1 text-sm mb-4"
          >
            <X className="h-4 w-4" />
            Cancel editing
          </Button>
          <h1 className="font-heading text-2xl font-semibold">
            Edit Job Profile
          </h1>
          <p className="text-muted-foreground">{profile.title}</p>
        </div>

        <JobProfileForm
          categories={categories}
          experienceLevels={experienceLevels}
          initialValues={buildInitialValues(profile)}
          onSubmit={handleUpdate}
          submitLabel="Save Changes"
          isSubmitting={isSubmitting}
        />
      </div>
    );
  }

  // ─── View mode ───────────────────────────────────────────────────────────
  return (
    <div className="w-full py-8">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/job-profiles"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Job Profiles
        </Link>

        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="font-heading text-2xl font-semibold">
                {profile.title}
              </h1>
            </div>
            <p className="text-muted-foreground text-sm">
              {(profile.organization as { name?: string })?.name}
            </p>
          </div>
          <div className="flex gap-2 shrink">
            <Button
              variant="outline"
              onClick={() => {
                const url = `${window.location.origin}/jobs/${jobId}`;
                navigator.clipboard.writeText(url);
                toast.success("Public URL copied to clipboard");
              }}
            >
              <LinkIcon className="mr-2 h-4 w-4" />
              Copy Public URL
            </Button>
            {hasSubmissions ? (
              <Button
                variant="outline"
                disabled
                title="Editing is disabled because this job profile has submissions"
              >
                <Lock className="mr-2 h-4 w-4" />
                Edit
              </Button>
            ) : (
              <Button variant="outline" onClick={() => setIsEditMode(true)}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </Button>
            )}
            <div className="flex items-center gap-2 border rounded-md px-3 h-9">
              {isTogglingActive ? (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              ) : (
                <Switch
                  id="is_active_toggle"
                  checked={isActive}
                  onCheckedChange={handleToggleActive}
                  disabled={isTogglingActive}
                />
              )}
              <Label
                htmlFor="is_active_toggle"
                className="text-sm cursor-pointer select-none"
              >
                Accepting applications
              </Label>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={(val) => router.replace(`?tab=${val}`)}
        className="mt-2"
      >
        <TabsList>
          <TabsTrigger value="details">
            <List className="h-4 w-4 mr-1.5" />
            Details
          </TabsTrigger>
          <TabsTrigger value="applications">
            <FileText className="h-4 w-4 mr-1.5" />
            Applications
          </TabsTrigger>
          <TabsTrigger value="results">
            <Star className="h-4 w-4 mr-1.5" />
            Results
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <BarChart3 className="h-4 w-4 mr-1.5" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="details" className="mt-4">
          {/* Meta badges */}
          <div className="mb-6 flex flex-wrap gap-2">
            {profile.category && (
              <Badge variant="secondary">
                {(profile.category as { title?: string })?.title}
              </Badge>
            )}
            {profile.experience_level && (
              <Badge variant="outline">
                {(profile.experience_level as { title?: string })?.title}
              </Badge>
            )}
            {profile.employment_type && (
              <Badge variant="outline">
                {EMPLOYMENT_TYPE_LABELS[profile.employment_type] ??
                  profile.employment_type}
              </Badge>
            )}
          </div>

          {/* Description */}
          <Card className="mb-4">
            <CardHeader>
              <CardTitle className="text-base">Description</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm whitespace-pre-wrap text-muted-foreground leading-relaxed">
                {profile.description}
              </p>
            </CardContent>
          </Card>

          {/* Qualifications */}
          {qualifications.length > 0 && (
            <Card className="mb-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <List className="h-4 w-4" />
                  Qualifications
                  <Badge variant="secondary" className="text-xs font-normal">
                    {qualifications.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <QualificationsDisplay qualifications={qualifications} />
              </CardContent>
            </Card>
          )}

          {/* Questions */}
          {profile.questions && profile.questions.length > 0 && (
            <Card className="mb-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <MessageSquare className="h-4 w-4" />
                  Application Questions
                  <Badge variant="secondary" className="text-xs font-normal">
                    {profile.questions.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {profile.questions.map((q, i) => (
                  <div key={q.id ?? i}>
                    {i > 0 && <Separator className="mb-4" />}
                    <div className="space-y-2">
                      <div className="flex items-start gap-2">
                        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium shrink-0">
                          {i + 1}
                        </span>
                        <p className="text-sm font-medium">{q.text}</p>
                      </div>
                      <div className="ml-8 flex flex-wrap items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {QUESTION_TYPE_LABELS[q.question_type ?? "text"] ??
                            q.question_type}
                        </Badge>
                        {q.is_required ? (
                          <Badge variant="secondary" className="text-xs">
                            Required
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs">
                            Optional
                          </Badge>
                        )}
                      </div>
                      {q.choices && q.choices.length > 0 && (
                        <ul className="ml-8 mt-1 space-y-1">
                          {q.choices.map((c, ci) => (
                            <li
                              key={ci}
                              className="flex items-center gap-2 text-sm text-muted-foreground"
                            >
                              <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground shrink-0" />
                              {c}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Footer meta */}
          <div className="mt-6 text-xs text-muted-foreground space-y-1">
            {profile.created_at && (
              <p>
                Created {new Date(profile.created_at).toLocaleDateString()}{" "}
                {profile.created_by && (
                  <>
                    by{" "}
                    {
                      (profile.created_by as { first_name?: string })
                        ?.first_name
                    }{" "}
                    {(profile.created_by as { last_name?: string })?.last_name}
                  </>
                )}
              </p>
            )}
            {profile.updated_at && (
              <p>
                Last updated {new Date(profile.updated_at).toLocaleDateString()}
              </p>
            )}
          </div>
        </TabsContent>

        <TabsContent value="applications" className="mt-4">
          <ApplicationsTab
            orgId={(profile.organization as { id?: string })?.id ?? ""}
            jobProfileId={jobId}
          />
        </TabsContent>

        <TabsContent value="results" className="mt-4">
          <ResultsTab
            orgId={(profile.organization as { id?: string })?.id ?? ""}
            jobProfileId={jobId}
          />
        </TabsContent>

        <TabsContent value="analytics" className="mt-4">
          <AnalyticsTab
            orgId={(profile.organization as { id?: string })?.id ?? ""}
            jobProfileId={jobId}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
