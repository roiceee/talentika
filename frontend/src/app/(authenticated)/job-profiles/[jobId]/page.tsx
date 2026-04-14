"use client";

import { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import {
  getJobProfile,
  updateJobProfile,
  deleteJobProfile,
  listOrgJobCategories,
  listOrgExperienceLevels,
  listMembers,
  createOrgJobCategory,
  createOrgExperienceLevel,
  type OrgRefItem,
} from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";
import type {
  JobProfileDetail,
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
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
  Trash2,
  MoreHorizontal,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export default function JobProfileDetailPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeTab = searchParams.get("tab") ?? "details";
  const { user } = useAuth();

  const [profile, setProfile] = useState<JobProfileDetail | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [categories, setCategories] = useState<OrgRefItem[]>([]);
  const [experienceLevels, setExperienceLevels] = useState<OrgRefItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditMode, setIsEditMode] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTogglingActive, setIsTogglingActive] = useState(false);
  const [isDeletingProfile, setIsDeletingProfile] = useState(false);
  const [deleteProfileDialogOpen, setDeleteProfileDialogOpen] = useState(false);
  const [deleteProfileConfirm, setDeleteProfileConfirm] = useState("");

  const fetchAll = useCallback(async () => {
    try {
      const prof = await getJobProfile(jobId);
      setProfile(prof);
      const orgId = (prof.organization as { id?: string })?.id;
      if (orgId) {
        const [cats, levels, members] = await Promise.all([
          listOrgJobCategories(orgId),
          listOrgExperienceLevels(orgId),
          listMembers(orgId),
        ]);
        setCategories(cats ?? []);
        setExperienceLevels(levels ?? []);
        const myMembership = members.find((m) => m.user?.id === user?.id);
        setIsAdmin(myMembership?.role === "ORG_ADMIN");
      }
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

  async function handleCreateCategory(
    title: string,
  ): Promise<{ id: string; title: string } | null> {
    const orgId = (profile?.organization as { id?: string })?.id;
    if (!orgId) return null;
    try {
      const created = await createOrgJobCategory(orgId, title);
      toast.success(`Category "${created.title}" created`);
      return created;
    } catch (error) {
      if (error instanceof AxiosError) {
        const msg =
          error.response?.data?.title?.[0] || "Failed to create category";
        toast.error(msg);
      } else {
        toast.error("Failed to create category");
      }
      return null;
    }
  }

  async function handleCreateExperienceLevel(
    title: string,
  ): Promise<{ id: string; title: string } | null> {
    const orgId = (profile?.organization as { id?: string })?.id;
    if (!orgId) return null;
    try {
      const created = await createOrgExperienceLevel(orgId, title);
      toast.success(`Experience level "${created.title}" created`);
      return created;
    } catch (error) {
      if (error instanceof AxiosError) {
        const msg =
          error.response?.data?.title?.[0] || "Failed to create experience level";
        toast.error(msg);
      } else {
        toast.error("Failed to create experience level");
      }
      return null;
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
          onCreateCategory={handleCreateCategory}
          onCreateExperienceLevel={handleCreateExperienceLevel}
        />
      </div>
    );
  }

  // ─── View mode ───────────────────────────────────────────────────────────
  return (
    <div className="w-full py-8">
      {/* Header */}
      <div className="page-header">
        <Link
          href="/job-profiles"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Job Profiles
        </Link>

        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="font-heading text-2xl">
                {profile.title}
              </h1>
              <Badge
                variant={isActive ? "default" : "secondary"}
                className={isActive ? "bg-emerald-600 text-white hover:bg-emerald-700" : ""}
              >
                {isActive ? "Accepting" : "Closed"}
              </Badge>
            </div>
            <p className="text-muted-foreground text-sm">
              {(profile.organization as { name?: string })?.name}
              {applicationCount > 0 && (
                <span className="ml-2 text-primary font-medium">
                  · {applicationCount} application{applicationCount !== 1 ? "s" : ""}
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-2 shrink-0 flex-wrap justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const url = `${window.location.origin}/jobs/${jobId}`;
                navigator.clipboard.writeText(url);
                toast.success("Public URL copied to clipboard");
              }}
              className="gap-2"
            >
              <LinkIcon className="h-3.5 w-3.5" />
              Copy URL
            </Button>
            {isAdmin && (
              <>
                {hasSubmissions ? (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-muted-foreground cursor-not-allowed gap-2"
                      >
                        <Lock className="h-3.5 w-3.5" />
                        Edit
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>
                        Editing is disabled because this job profile has
                        submissions.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                ) : (
                  <Button variant="outline" size="sm" onClick={() => setIsEditMode(true)} className="gap-2">
                    <Pencil className="h-3.5 w-3.5" />
                    Edit
                  </Button>
                )}
                <div className={`flex items-center gap-2 border rounded-md px-3 h-9 transition-colors ${isActive ? "border-emerald-200 bg-emerald-50" : ""}`}>
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
                    {isActive ? "Accepting" : "Closed"}
                  </Label>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-9 w-9">
                      {isDeletingProfile ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <MoreHorizontal className="h-4 w-4" />
                      )}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      className="text-destructive focus:text-destructive focus:bg-destructive/10"
                      onSelect={() => {
                        setDeleteProfileConfirm("");
                        setDeleteProfileDialogOpen(true);
                      }}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete job profile
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                <Dialog
                  open={deleteProfileDialogOpen}
                  onOpenChange={(open) => {
                    if (!isDeletingProfile) setDeleteProfileDialogOpen(open);
                  }}
                >
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Delete job profile?</DialogTitle>
                      <DialogDescription>
                        This will permanently delete &quot;{profile.title}&quot; and
                        all associated applications. This action cannot be undone.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-2">
                      <Label htmlFor="confirm-delete-profile" className="text-sm">
                        Type <span className="font-semibold">confirm deletion</span> to proceed
                      </Label>
                      <Input
                        id="confirm-delete-profile"
                        value={deleteProfileConfirm}
                        onChange={(e) => setDeleteProfileConfirm(e.target.value)}
                        placeholder="confirm deletion"
                        autoComplete="off"
                      />
                    </div>
                    <DialogFooter>
                      <Button
                        variant="outline"
                        onClick={() => setDeleteProfileDialogOpen(false)}
                        disabled={isDeletingProfile}
                      >
                        Cancel
                      </Button>
                      <Button
                        variant="destructive"
                        disabled={deleteProfileConfirm !== "confirm deletion" || isDeletingProfile}
                        onClick={async () => {
                          const orgId = (profile.organization as { id?: string })?.id;
                          if (!orgId) return;
                          setIsDeletingProfile(true);
                          try {
                            await deleteJobProfile(orgId, jobId);
                            toast.success("Job profile deleted");
                            router.push("/job-profiles");
                          } catch (error) {
                            if (error instanceof AxiosError) {
                              const data = error.response?.data;
                              toast.error(data?.error ?? data?.detail ?? "Failed to delete job profile");
                            } else {
                              toast.error("Failed to delete job profile");
                            }
                            setIsDeletingProfile(false);
                            setDeleteProfileDialogOpen(false);
                          }
                        }}
                      >
                        {isDeletingProfile && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Delete
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={(val) => router.replace(`?tab=${val}`)}
        className="mt-2"
      >
        <TabsList className="bg-muted/60 border border-border/50">
          <TabsTrigger value="details" className="gap-1.5 data-[state=active]:text-primary">
            <List className="h-3.5 w-3.5" />
            Details
          </TabsTrigger>
          <TabsTrigger value="applications" className="gap-1.5 data-[state=active]:text-primary">
            <FileText className="h-3.5 w-3.5" />
            Applications
            {applicationCount > 0 && (
              <span className="ml-0.5 rounded-full bg-primary/15 text-primary text-[10px] px-1.5 py-0.5 font-medium leading-none">
                {applicationCount}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="results" className="gap-1.5 data-[state=active]:text-primary">
            <Star className="h-3.5 w-3.5" />
            Results
          </TabsTrigger>
          <TabsTrigger value="analytics" className="gap-1.5 data-[state=active]:text-primary">
            <BarChart3 className="h-3.5 w-3.5" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="details" className="mt-4">
          {/* Meta badges */}
          <div className="mb-6 flex flex-wrap gap-2">
            {profile.category && (
              <Badge variant="secondary">{profile.category?.title}</Badge>
            )}
            {profile.experience_level && (
              <Badge variant="outline">{profile.experience_level?.title}</Badge>
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
            hasRequiredQuestions={profile.questions?.some((q) => q.is_required) ?? false}
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
            basePath={`/job-profiles/${jobId}`}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
