"use client";

import { use, useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import {
  getJobApplication,
  getJobProfile,
  getResumeDownloadUrl,
  updateApplicationStatus,
} from "@/lib/api";
import type {
  JobApplicationDetailWithAnalysis,
  JobProfileDetail,
} from "@/lib/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  User,
  FileText,
  Download,
  MessageSquare,
  Loader2,
} from "lucide-react";

const UPDATABLE_STATUSES = [
  { value: "to_be_reviewed", label: "To Be Reviewed" },
  { value: "reviewed", label: "Reviewed" },
  { value: "shortlisted", label: "Shortlisted" },
  { value: "rejected", label: "Rejected" },
] as const;

const QUESTION_TYPE_LABELS: Record<string, string> = {
  text: "Text",
  mcq: "Multiple Choice (multi)",
  mcq_single: "Multiple Choice (single)",
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
    } catch {
      toast.error("Failed to update status");
    } finally {
      setIsUpdatingStatus(false);
    }
  }
  const answers: AnswerItem[] =
    typeof application.answers === "string"
      ? []
      : ((application.answers as unknown as AnswerItem[]) ?? []);
  const resumeAttachment = application.attachments?.find(
    (a) => a.file_type === "resume",
  );

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
            <div className="flex items-center gap-2">
              <Select
                value={application.status ?? "to_be_reviewed"}
                onValueChange={handleStatusChange}
                disabled={isUpdatingStatus}
              >
                <SelectTrigger className="h-8 w-40 text-xs">
                  {isUpdatingStatus ? (
                    <span className="text-muted-foreground">Updating…</span>
                  ) : (
                    <SelectValue />
                  )}
                </SelectTrigger>
                <SelectContent>
                  {UPDATABLE_STATUSES.map((s) => (
                    <SelectItem
                      key={s.value}
                      value={s.value}
                      className={
                        s.value === "shortlisted"
                          ? "text-emerald-600 font-medium focus:text-emerald-600"
                          : s.value === "rejected"
                            ? "text-destructive focus:text-destructive"
                            : ""
                      }
                    >
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
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
    </div>
  );
}
