"use client";

import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { AxiosError } from "axios";
import { getJobApplication, getResumeDownloadUrl } from "@/lib/api";
import type { JobApplicationDetailWithAnalysis } from "@/lib/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
} from "lucide-react";
import { QUESTION_TYPE_LABELS } from "@/lib/constants/job-profile";

const STATUS_CONFIG: Record<
  string,
  {
    label: string;
    variant: "default" | "secondary" | "outline" | "destructive";
  }
> = {
  submitted: { label: "Submitted", variant: "secondary" },
  under_review: { label: "Under Review", variant: "default" },
  shortlisted: { label: "Shortlisted", variant: "default" },
  rejected: { label: "Rejected", variant: "destructive" },
};

interface ApplicationDetailViewProps {
  orgId: string;
  jobProfileId: string;
  applicationId: string;
  onBack: () => void;
}

type AnswerItem = {
  question_id: string;
  question_text: string;
  question_type: string;
  choices: string[];
  is_required: boolean;
  answer_text: string | null;
  selected_choices: string[] | null;
};

export function ApplicationDetailView({
  orgId,
  jobProfileId,
  applicationId,
  onBack,
}: ApplicationDetailViewProps) {
  const [application, setApplication] =
    useState<JobApplicationDetailWithAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [resumeUrl, setResumeUrl] = useState<string | null>(null);

  const fetchApplication = useCallback(async () => {
    try {
      const data = await getJobApplication(orgId, jobProfileId, applicationId);
      setApplication(data);

      // Check if there's a resume attachment
      const resume = data.attachments?.find((a) => a.file_type === "resume");
      if (resume) {
        setResumeUrl(getResumeDownloadUrl(orgId, jobProfileId, applicationId));
      }
    } catch (error) {
      if (error instanceof AxiosError && error.response?.status === 404) {
        toast.error("Application not found");
      } else {
        toast.error("Failed to load application");
      }
      onBack();
    } finally {
      setIsLoading(false);
    }
  }, [orgId, jobProfileId, applicationId, onBack]);

  useEffect(() => {
    fetchApplication();
  }, [fetchApplication]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-48 w-full rounded-lg" />
        <Skeleton className="h-32 w-full rounded-lg" />
        <Skeleton className="h-64 w-full rounded-lg" />
      </div>
    );
  }

  if (!application) return null;

  const statusConfig = STATUS_CONFIG[application.status ?? "submitted"];
  const address = application.address;
  // answers comes as a serialized field — it's actually an array
  const answers: AnswerItem[] =
    typeof application.answers === "string"
      ? []
      : ((application.answers as unknown as AnswerItem[]) ?? []);
  const resumeAttachment = application.attachments?.find(
    (a) => a.file_type === "resume",
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={onBack}
          className="inline-flex items-center gap-1"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Applications
        </Button>
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
            <Badge variant={statusConfig?.variant ?? "secondary"}>
              {statusConfig?.label ?? application.status}
            </Badge>
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
                <Button variant="outline" size="sm" asChild>
                  <a href={resumeUrl} download={resumeAttachment.file_name}>
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </a>
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
                  className="w-full h-[800px]"
                  title="Resume Preview"
                />
              </div>
            ) : resumeUrl ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <FileText className="h-12 w-12 text-muted-foreground/40 mb-3" />
                <p className="text-sm text-muted-foreground mb-2">
                  Preview is not available for this file type.
                </p>
                <Button variant="outline" size="sm" asChild>
                  <a href={resumeUrl} download={resumeAttachment.file_name}>
                    <Download className="mr-2 h-4 w-4" />
                    Download to view
                  </a>
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
