"use client";

import { use, useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import {
  getJobApplication,
  getJobProfile,
  getResumeDownloadUrl,
  updateApplicationStatus,
  retryAnalysis,
  listJobApplications,
} from "@/lib/api";
import type {
  JobApplicationDetailWithAnalysis,
  JobProfileDetail,
} from "@/lib/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApplicationStatusActions } from "@/components/application-status-actions";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Mail,
  Phone,
  MapPin,
  User,
  FileText,
  Download,
  MessageSquare,
  Loader2,
  Brain,
  AlertCircle,
  Clock,
  RefreshCw,
  Star,
  Lightbulb,
  GraduationCap,
  Briefcase,
  Award,
  TrendingUp,
  TrendingDown,
  SlidersHorizontal,
} from "lucide-react";
import { QUESTION_TYPE_LABELS } from "@/lib/constants/job-profile";

type AnalysisData = {
  id?: string;
  status?: string;
  score_category?: { key: string; label: string } | null;
  ai_analysis_summary?: string;
  notable_traits?: string[];
  key_skills?: string[];
  detailed_analysis?: {
    strengths?: string[];
    areas_for_development?: string[];
    experience?: { title?: string; company?: string; duration?: string }[];
    education?: { degree?: string; institution?: string; year?: string }[];
    certifications?: string[];
  } | null;
  error_message?: string;
  created_at?: string;
  updated_at?: string;
};

type AnswerItem = {
  question_id: string;
  question_text: string;
  question_type: string;
  choices: string[];
  is_required: boolean;
  answer_text: string | null;
  selected_choices: string[] | null;
};

export default function ApplicationDetailPage({
  params,
}: {
  params: Promise<{ jobId: string; applicationId: string }>;
}) {
  const { jobId, applicationId } = use(params);
  const router = useRouter();

  const [application, setApplication] =
    useState<JobApplicationDetailWithAnalysis | null>(null);
  const [profile, setProfile] = useState<JobProfileDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [resumeUrl, setResumeUrl] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [orgId, setOrgId] = useState<string>("");
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  // undefined = not yet fetched, null = none, string = app id
  const [nextApplicationId, setNextApplicationId] = useState<
    string | null | undefined
  >(undefined);
  const [prevApplicationId, setPrevApplicationId] = useState<
    string | null | undefined
  >(undefined);
  const [analysisCollapsed, setAnalysisCollapsed] = useState(false);

  async function fetchNextUnreviewed(resolvedOrgId: string) {
    try {
      const result = await listJobApplications(resolvedOrgId, jobId, {
        status: "to_be_reviewed",
        page_size: 100,
        ordering: "submitted_at",
      });
      const apps = result.results;
      if (apps.length === 0) {
        setPrevApplicationId(null);
        setNextApplicationId(null);
        return;
      }
      const idx = apps.findIndex((a) => a.id === applicationId);
      if (idx === -1) {
        setPrevApplicationId(null);
        setNextApplicationId(apps[0]?.id ?? null);
      } else {
        setPrevApplicationId(apps[idx - 1]?.id ?? null);
        // Wrap around to first if at end
        setNextApplicationId(apps[idx + 1]?.id ?? apps[0]?.id ?? null);
      }
    } catch {
      setPrevApplicationId(null);
      setNextApplicationId(null);
    }
  }

  async function handleDownload(fileName: string) {
    if (!resumeUrl || isDownloading) return;
    setIsDownloading(true);
    try {
      const res = await fetch(resumeUrl);
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Failed to download resume");
    } finally {
      setIsDownloading(false);
    }
  }

  const fetchData = useCallback(async () => {
    try {
      const prof = await getJobProfile(jobId);
      setProfile(prof);

      const resolvedOrgId = (prof.organization as { id?: string })?.id ?? "";
      setOrgId(resolvedOrgId);
      const data = await getJobApplication(resolvedOrgId, jobId, applicationId);
      setApplication(data);
      fetchNextUnreviewed(resolvedOrgId);

      const resume = data.attachments?.find((a) => a.file_type === "resume");
      if (resume) {
        setResumeUrl(getResumeDownloadUrl(resolvedOrgId, jobId, applicationId));
      }
    } catch (error) {
      if (error instanceof AxiosError) {
        if (error.response?.status === 404) {
          toast.error("Application not found");
        } else if (error.response?.status === 403) {
          toast.error("You don't have permission to view this application");
        } else {
          toast.error("Failed to load application");
        }
      } else {
        toast.error("Failed to load application");
      }
      router.push(`/job-profiles/${jobId}`);
    } finally {
      setIsLoading(false);
    }
  }, [jobId, applicationId, router]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Poll every 5 seconds while analysis is still processing
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const analysisRaw = (application?.analysis ??
      null) as unknown as AnalysisData | null;
    const isProcessing =
      analysisRaw?.status && !["done", "failed"].includes(analysisRaw.status);

    if (isProcessing && orgId) {
      if (!pollRef.current) {
        pollRef.current = setInterval(async () => {
          try {
            const data = await getJobApplication(orgId, jobId, applicationId);
            setApplication(data);
          } catch {
            // silently ignore poll errors
          }
        }, 5000);
      }
    } else if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [application, orgId, jobId, applicationId]);

  if (isLoading) {
    return (
      <div className="w-full py-8 space-y-4">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-48 w-full rounded-lg" />
        <Skeleton className="h-32 w-full rounded-lg" />
        <Skeleton className="h-64 w-full rounded-lg" />
      </div>
    );
  }

  if (!application || !profile) return null;

  const address = application.address;

  async function handleStatusChange(newStatus: string) {
    if (!orgId || isUpdatingStatus) return;
    setIsUpdatingStatus(true);
    try {
      const updated = await updateApplicationStatus(
        orgId,
        jobId,
        applicationId,
        newStatus as "to_be_reviewed" | "reviewed" | "shortlisted" | "rejected",
      );
      setApplication((prev) =>
        prev ? { ...prev, status: updated.status } : prev,
      );
      toast.success("Status updated");
      fetchNextUnreviewed(orgId);
    } catch {
      toast.error("Failed to update status");
    } finally {
      setIsUpdatingStatus(false);
    }
  }
  const analysis = (application.analysis ??
    null) as unknown as AnalysisData | null;
  const answers: AnswerItem[] =
    typeof application.answers === "string"
      ? []
      : ((application.answers as unknown as AnswerItem[]) ?? []);
  const resumeAttachment = application.attachments?.find(
    (a) => a.file_type === "resume",
  );

  async function handleStatusAction(status: string, andNext: boolean) {
    await handleStatusChange(status);
    if (andNext) {
      if (nextApplicationId) {
        router.push(`/job-profiles/${jobId}/applications/${nextApplicationId}`);
      } else {
        router.push(`/job-profiles/${jobId}?tab=results`);
      }
    }
  }

  async function handleRetryAnalysis() {
    if (!application?.id || isRetrying) return;
    setIsRetrying(true);
    try {
      await retryAnalysis(application.id);
      toast.success("Analysis re-triggered");
      setApplication((prev) =>
        prev
          ? {
              ...prev,
              analysis: JSON.stringify({
                ...(analysis ?? {}),
                status: "uploaded",
                error_message: "",
              }),
            }
          : prev,
      );
    } catch {
      toast.error("Failed to retry analysis");
    } finally {
      setIsRetrying(false);
    }
  }

  return (
    <div className="w-full py-8 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link
          href={`/job-profiles/${jobId}?tab=applications`}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to {profile.title}
        </Link>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            disabled={!prevApplicationId}
            onClick={() =>
              router.push(
                `/job-profiles/${jobId}/applications/${prevApplicationId}`,
              )
            }
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Prev
          </Button>
          <Button
            size="sm"
            variant={nextApplicationId === null ? "outline" : "default"}
            disabled={nextApplicationId === undefined}
            onClick={() =>
              nextApplicationId
                ? router.push(
                    `/job-profiles/${jobId}/applications/${nextApplicationId}`,
                  )
                : router.push(`/job-profiles/${jobId}?tab=results`)
            }
          >
            {nextApplicationId === undefined ? (
              <Loader2 className="h-4 w-4 animate-spin mr-1" />
            ) : (
              <>
                {nextApplicationId === null ? "View Results" : "Next"}
                <ChevronRight className="h-4 w-4 ml-1" />
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Applicant Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                <User className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <CardTitle className="text-lg">
                  {application.first_name} {application.last_name}
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  Applied{" "}
                  {application.submitted_at
                    ? new Date(application.submitted_at).toLocaleDateString(
                        undefined,
                        {
                          year: "numeric",
                          month: "long",
                          day: "numeric",
                        },
                      )
                    : "—"}
                </p>
              </div>
            </div>
            <ApplicationStatusActions
              currentStatus={application.status}
              isUpdating={isUpdatingStatus}
              onAction={handleStatusAction}
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="flex items-center gap-2 text-sm">
              <Mail className="h-4 w-4 text-muted-foreground shrink-0" />
              <a
                href={`mailto:${application.email}`}
                className="text-primary hover:underline"
              >
                {application.email}
              </a>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Phone className="h-4 w-4 text-muted-foreground shrink-0" />
              <span>{application.phone}</span>
            </div>
          </div>
          {address && (
            <div className="flex items-start gap-2 text-sm">
              <MapPin className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
              <span>
                {[
                  address.line1,
                  address.line2,
                  address.city,
                  address.province_state,
                  address.postal_code,
                  address.country,
                ]
                  .filter(Boolean)
                  .join(", ")}
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Answers */}
      {answers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <MessageSquare className="h-4 w-4" />
              Application Answers
              <Badge variant="secondary" className="text-xs font-normal">
                {answers.length}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {answers.map((answer, i) => (
              <div key={answer.question_id}>
                {i > 0 && <Separator className="mb-4" />}
                <div className="space-y-2">
                  <div className="flex items-start gap-2">
                    <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium shrink-0">
                      {i + 1}
                    </span>
                    <div className="flex-1 space-y-1">
                      <p className="text-sm font-medium">
                        {answer.question_text}
                        {answer.is_required && (
                          <span className="text-destructive ml-1">*</span>
                        )}
                      </p>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {QUESTION_TYPE_LABELS[answer.question_type] ??
                            answer.question_type}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="ml-8 mt-1">
                    {answer.question_type === "text" ? (
                      <p className="text-sm text-muted-foreground bg-muted/50 rounded-md px-3 py-2">
                        {answer.answer_text || (
                          <span className="italic">No answer provided</span>
                        )}
                      </p>
                    ) : (
                      <div className="space-y-1">
                        {answer.choices?.map((choice, ci) => {
                          const isSelected =
                            answer.selected_choices?.includes(choice);
                          return (
                            <div
                              key={ci}
                              className={`flex items-center gap-2 text-sm rounded-md px-3 py-1.5 ${
                                isSelected
                                  ? "bg-primary/10 text-primary font-medium"
                                  : "text-muted-foreground"
                              }`}
                            >
                              <span
                                className={`h-2 w-2 rounded-full shrink-0 ${
                                  isSelected
                                    ? "bg-primary"
                                    : "bg-muted-foreground/30"
                                }`}
                              />
                              {choice}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* AI Analysis */}
      {analysis && (
        <Card>
          <CardHeader
            className="pb-4 cursor-pointer select-none"
            onClick={() => setAnalysisCollapsed((v) => !v)}
          >
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <Brain className="h-4 w-4" />
                AI Analysis
                {analysis.status === "done" ? (
                  <Badge className="bg-emerald-600 text-white hover:bg-emerald-700 text-xs">
                    Complete
                  </Badge>
                ) : analysis.status === "failed" ? (
                  <Badge variant="destructive" className="text-xs">
                    Failed
                  </Badge>
                ) : (
                  <Badge
                    variant="secondary"
                    className="flex items-center gap-1 text-xs"
                  >
                    {analysis.status === "ocr_pending" ||
                    analysis.status === "ai_pending" ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Clock className="h-3 w-3" />
                    )}
                    {analysis.status === "uploaded"
                      ? "Queued"
                      : analysis.status === "ocr_pending"
                        ? "OCR Processing"
                        : analysis.status === "ocr_done"
                          ? "OCR Done"
                          : analysis.status === "ai_pending"
                            ? "AI Analyzing"
                            : analysis.status}
                  </Badge>
                )}
              </CardTitle>
              <div
                className="flex items-center gap-2"
                onClick={(e) => e.stopPropagation()}
              >
                {analysisCollapsed ? (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronUp className="h-4 w-4 text-muted-foreground" />
                )}
                {analysis.status === "failed" && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRetryAnalysis}
                    disabled={isRetrying}
                  >
                    {isRetrying ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="mr-2 h-4 w-4" />
                    )}
                    Retry
                  </Button>
                )}
                {/* Allow retry for stuck processing states */}
                {analysis.status &&
                  !["done", "failed"].includes(analysis.status) && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleRetryAnalysis}
                      disabled={isRetrying}
                      title="Restart analysis if stuck"
                    >
                      {isRetrying ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="mr-2 h-4 w-4" />
                      )}
                      Restart
                    </Button>
                  )}
              </div>
            </div>
          </CardHeader>
          {!analysisCollapsed && (
            <CardContent className="space-y-6">
              {/* Category hero row */}
              <div className="flex items-center gap-4">
                {analysis.status === "done" && analysis.score_category && (
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex items-center justify-center h-14 px-4 rounded-full border-4 ${
                        {
                          excellent: "border-emerald-500 text-emerald-600",
                          good: "border-blue-400 text-blue-600",
                          moderate: "border-amber-400 text-amber-600",
                          bad: "border-red-400 text-destructive",
                        }[analysis.score_category.key] ??
                        "border-muted text-muted-foreground"
                      }`}
                    >
                      <span className="text-lg font-bold">
                        {analysis.score_category.label}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Error message */}
              {analysis.status === "failed" && analysis.error_message && (
                <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3">
                  <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
                  <p className="text-sm text-destructive">
                    {analysis.error_message}
                  </p>
                </div>
              )}

              {/* Processing message */}
              {analysis.status &&
                !["done", "failed"].includes(analysis.status) && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 rounded-md px-4 py-3">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>
                      Analysis is in progress. This page will update
                      automatically.
                    </span>
                  </div>
                )}

              {/* Done — full analysis */}
              {analysis.status === "done" && (
                <>
                  {/* Summary */}
                  {analysis.ai_analysis_summary && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-semibold flex items-center gap-1.5">
                        <Lightbulb className="h-4 w-4 text-amber-500" />
                        Summary
                      </h4>
                      <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap bg-muted/40 rounded-lg px-4 py-3">
                        {analysis.ai_analysis_summary}
                      </p>
                    </div>
                  )}

                  {/* Skills & Traits side-by-side */}
                  {((analysis.key_skills && analysis.key_skills.length > 0) ||
                    (analysis.notable_traits &&
                      analysis.notable_traits.length > 0)) && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Key Skills */}
                      {analysis.key_skills &&
                        analysis.key_skills.length > 0 && (
                          <div className="space-y-2 bg-muted/30 rounded-lg p-4">
                            <h4 className="text-sm font-semibold flex items-center gap-1.5">
                              <Star className="h-4 w-4 text-blue-500" />
                              Key Skills
                            </h4>
                            <div className="flex flex-wrap gap-1.5">
                              {(analysis.key_skills as unknown as string[]).map(
                                (skill, i) => (
                                  <Badge
                                    key={i}
                                    variant="secondary"
                                    className="text-xs"
                                  >
                                    {skill}
                                  </Badge>
                                ),
                              )}
                            </div>
                          </div>
                        )}

                      {/* Notable Traits */}
                      {analysis.notable_traits &&
                        analysis.notable_traits.length > 0 && (
                          <div className="space-y-2 bg-muted/30 rounded-lg p-4">
                            <h4 className="text-sm font-semibold flex items-center gap-1.5">
                              <Award className="h-4 w-4 text-purple-500" />
                              Notable Traits
                            </h4>
                            <div className="flex flex-wrap gap-1.5">
                              {(
                                analysis.notable_traits as unknown as string[]
                              ).map((trait, i) => (
                                <Badge
                                  key={i}
                                  variant="outline"
                                  className="text-xs"
                                >
                                  {trait}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                    </div>
                  )}

                  {/* Detailed Analysis */}
                  {analysis.detailed_analysis && (
                    <>
                      <Separator />

                      {/* Strengths & Areas for Development side-by-side */}
                      {((analysis.detailed_analysis.strengths &&
                        analysis.detailed_analysis.strengths.length > 0) ||
                        (analysis.detailed_analysis.areas_for_development &&
                          analysis.detailed_analysis.areas_for_development
                            .length > 0)) && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Strengths */}
                          {analysis.detailed_analysis.strengths &&
                            analysis.detailed_analysis.strengths.length > 0 && (
                              <div className="space-y-2 rounded-lg border border-emerald-200 bg-emerald-50/50 p-4">
                                <h4 className="text-sm font-semibold flex items-center gap-1.5 text-emerald-700">
                                  <TrendingUp className="h-4 w-4" />
                                  Strengths
                                </h4>
                                <ul className="space-y-1.5">
                                  {analysis.detailed_analysis.strengths.map(
                                    (s, i) => (
                                      <li
                                        key={i}
                                        className="text-sm text-emerald-800/80 flex items-start gap-2"
                                      >
                                        <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0" />
                                        {s}
                                      </li>
                                    ),
                                  )}
                                </ul>
                              </div>
                            )}

                          {/* Areas for Development */}
                          {analysis.detailed_analysis.areas_for_development &&
                            analysis.detailed_analysis.areas_for_development
                              .length > 0 && (
                              <div className="space-y-2 rounded-lg border border-amber-200 bg-amber-50/50 p-4">
                                <h4 className="text-sm font-semibold flex items-center gap-1.5 text-amber-700">
                                  <TrendingDown className="h-4 w-4" />
                                  Areas for Development
                                </h4>
                                <ul className="space-y-1.5">
                                  {analysis.detailed_analysis.areas_for_development.map(
                                    (a, i) => (
                                      <li
                                        key={i}
                                        className="text-sm text-amber-800/80 flex items-start gap-2"
                                      >
                                        <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0" />
                                        {a}
                                      </li>
                                    ),
                                  )}
                                </ul>
                              </div>
                            )}
                        </div>
                      )}

                      {/* Experience & Education side-by-side */}
                      {((analysis.detailed_analysis.experience &&
                        analysis.detailed_analysis.experience.length > 0) ||
                        (analysis.detailed_analysis.education &&
                          analysis.detailed_analysis.education.length > 0)) && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {/* Experience */}
                          {analysis.detailed_analysis.experience &&
                            analysis.detailed_analysis.experience.length >
                              0 && (
                              <div className="space-y-3">
                                <h4 className="text-sm font-semibold flex items-center gap-1.5">
                                  <Briefcase className="h-4 w-4 text-blue-500" />
                                  Experience
                                </h4>
                                <div className="space-y-2">
                                  {analysis.detailed_analysis.experience.map(
                                    (exp, i) => (
                                      <div
                                        key={i}
                                        className="text-sm rounded-lg border bg-card px-4 py-3"
                                      >
                                        <p className="font-medium">
                                          {exp.title}
                                        </p>
                                        {exp.company && (
                                          <p className="text-muted-foreground">
                                            {exp.company}
                                          </p>
                                        )}
                                        {exp.duration && (
                                          <p className="text-xs text-muted-foreground/80 mt-0.5">
                                            {exp.duration}
                                          </p>
                                        )}
                                      </div>
                                    ),
                                  )}
                                </div>
                              </div>
                            )}

                          {/* Education */}
                          {analysis.detailed_analysis.education &&
                            analysis.detailed_analysis.education.length > 0 && (
                              <div className="space-y-3">
                                <h4 className="text-sm font-semibold flex items-center gap-1.5">
                                  <GraduationCap className="h-4 w-4 text-indigo-500" />
                                  Education
                                </h4>
                                <div className="space-y-2">
                                  {analysis.detailed_analysis.education.map(
                                    (edu, i) => (
                                      <div
                                        key={i}
                                        className="text-sm rounded-lg border bg-card px-4 py-3"
                                      >
                                        <p className="font-medium">
                                          {edu.degree}
                                        </p>
                                        {edu.institution && (
                                          <p className="text-muted-foreground">
                                            {edu.institution}
                                          </p>
                                        )}
                                        {edu.year && (
                                          <p className="text-xs text-muted-foreground/80 mt-0.5">
                                            {edu.year}
                                          </p>
                                        )}
                                      </div>
                                    ),
                                  )}
                                </div>
                              </div>
                            )}
                        </div>
                      )}

                      {/* Certifications */}
                      {analysis.detailed_analysis.certifications &&
                        analysis.detailed_analysis.certifications.length >
                          0 && (
                          <div className="space-y-2">
                            <h4 className="text-sm font-semibold flex items-center gap-1.5">
                              <Award className="h-4 w-4 text-teal-500" />
                              Certifications
                            </h4>
                            <div className="flex flex-wrap gap-1.5">
                              {analysis.detailed_analysis.certifications.map(
                                (cert, i) => (
                                  <Badge
                                    key={i}
                                    variant="outline"
                                    className="text-xs"
                                  >
                                    {cert}
                                  </Badge>
                                ),
                              )}
                            </div>
                          </div>
                        )}
                    </>
                  )}
                </>
              )}
            </CardContent>
          )}
        </Card>
      )}

      {/* Resume */}
      {resumeAttachment && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="h-4 w-4" />
                Resume
              </CardTitle>
              {resumeUrl && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    handleDownload(resumeAttachment.file_name ?? "resume")
                  }
                  disabled={isDownloading}
                >
                  {isDownloading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="mr-2 h-4 w-4" />
                  )}
                  {isDownloading ? "Downloading…" : "Download"}
                </Button>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              {resumeAttachment.file_name}
              {resumeAttachment.file_size && (
                <span className="ml-2">
                  ({(resumeAttachment.file_size / 1024).toFixed(0)} KB)
                </span>
              )}
            </p>
          </CardHeader>
          <CardContent>
            {resumeUrl &&
            resumeAttachment.file_name?.toLowerCase().endsWith(".pdf") ? (
              <div className="w-full rounded-md border overflow-hidden">
                <iframe
                  src={resumeUrl}
                  className="w-full h-200"
                  title="Resume Preview"
                />
              </div>
            ) : resumeUrl ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <FileText className="h-12 w-12 text-muted-foreground/40 mb-3" />
                <p className="text-sm text-muted-foreground mb-2">
                  Preview is not available for this file type.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    handleDownload(resumeAttachment.file_name ?? "resume")
                  }
                  disabled={isDownloading}
                >
                  {isDownloading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="mr-2 h-4 w-4" />
                  )}
                  {isDownloading ? "Downloading…" : "Download to view"}
                </Button>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Resume file is not available for preview.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Floating action panel */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2 group/fab">
        {/* Expanded panel — visible on hover */}
        <div className="pointer-events-none opacity-0 translate-y-2 group-hover/fab:pointer-events-auto group-hover/fab:opacity-100 group-hover/fab:translate-y-0 transition-all duration-200">
          <Card className="shadow-xl border w-52">
            <CardContent className="p-3 flex flex-col gap-2">
              {/* Navigation */}
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  disabled={!prevApplicationId}
                  onClick={() =>
                    router.push(
                      `/job-profiles/${jobId}/applications/${prevApplicationId}`,
                    )
                  }
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Prev
                </Button>
                <Button
                  size="sm"
                  variant={nextApplicationId === null ? "outline" : "default"}
                  className="flex-1"
                  disabled={nextApplicationId === undefined}
                  onClick={() =>
                    nextApplicationId
                      ? router.push(
                          `/job-profiles/${jobId}/applications/${nextApplicationId}`,
                        )
                      : router.push(`/job-profiles/${jobId}?tab=results`)
                  }
                >
                  {nextApplicationId === null ? "Results" : "Next"}
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>

              <Separator />

              {/* Status actions */}
              <ApplicationStatusActions
                currentStatus={application.status}
                isUpdating={isUpdatingStatus}
                onAction={handleStatusAction}
                vertical
              />
            </CardContent>
          </Card>
        </div>

        {/* Trigger button */}
        <Button size="icon" className="h-12 w-12 rounded-full shadow-lg">
          {isUpdatingStatus ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <SlidersHorizontal className="h-5 w-5" />
          )}
        </Button>
      </div>
    </div>
  );
}
