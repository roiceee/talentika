"use client";

import { useEffect, useState, useCallback, use } from "react";
import { toast } from "sonner";
import { AxiosError } from "axios";
import {
  getPublicJobProfile,
  submitApplication,
  uploadResume,
  getCountries,
  getStates,
  getCities,
  type GeoCountry,
  type GeoState,
  type GeoCity,
} from "@/lib/api";
import type {
  JobApplicationCreate,
  JobProfileDetail,
  Question,
  Qualification,
} from "@/lib/client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Briefcase,
  MapPin,
  Upload,
  FileText,
  CheckCircle2,
  XCircle,
  Loader2,
  List,
} from "lucide-react";
import { LocationCombobox } from "@/components/jobs/location-combobox";
import { QuestionField } from "@/components/jobs/question-field";
import { PhoneInput } from "@/components/jobs/phone-input";
import { QualificationsDisplay } from "@/components/qualifications-display";
import { EMPLOYMENT_TYPE_LABELS } from "@/lib/constants/job-profile";

export default function PublicJobProfilePage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = use(params);

  const [profile, setProfile] = useState<JobProfileDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  // Form state
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [dialCode, setDialCode] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");

  // Address — store ISO codes for API, display names for UI
  const [line1, setLine1] = useState("");
  const [line2, setLine2] = useState("");
  const [countryCode, setCountryCode] = useState(""); // ISO-2, sent to backend
  const [stateCode, setStateCode] = useState(""); // state ISO code
  const [cityName, setCityName] = useState("");
  const [postalCode, setPostalCode] = useState("");

  // Location options (async loaded)
  const [countryOptions, setCountryOptions] = useState<GeoCountry[]>([]);
  const [stateOptions, setStateOptions] = useState<GeoState[]>([]);
  const [cityOptions, setCityOptions] = useState<GeoCity[]>([]);

  // Load countries once on mount
  useEffect(() => {
    getCountries().then(setCountryOptions);
  }, []);

  // Reload states when countryCode changes
  useEffect(() => {
    if (!countryCode) {
      setStateOptions([]);
      return;
    }
    getStates(countryCode).then(setStateOptions);
  }, [countryCode]);

  // Reload cities when stateCode changes
  useEffect(() => {
    if (!countryCode || !stateCode) {
      setCityOptions([]);
      return;
    }
    getCities(countryCode, stateCode).then(setCityOptions);
  }, [countryCode, stateCode]);

  // Question answers: key = question id, value = answer
  const [textAnswers, setTextAnswers] = useState<Record<string, string>>({});
  const [mcqAnswers, setMcqAnswers] = useState<Record<string, string[]>>({});

  // Resume upload
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDraggingOver, setIsDraggingOver] = useState(false);

  // Submission
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const fetchProfile = useCallback(async () => {
    try {
      const data = await getPublicJobProfile(jobId);
      if (!data.is_active) {
        setNotFound(true);
        return;
      }
      setProfile(data);
    } catch (error) {
      if (
        error instanceof AxiosError &&
        (error.response?.status === 404 || error.response?.status === 403)
      ) {
        setNotFound(true);
      } else {
        toast.error("Failed to load job profile");
      }
    } finally {
      setIsLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  // Handle resume file selection & upload
  async function processResumeFile(file: File) {
    // Validate file type (check MIME type AND extension — MIME can be unreliable)
    const allowedTypes = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    const allowedExtensions = [".pdf", ".doc", ".docx"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(ext)) {
      setUploadError("Only PDF, DOC, and DOCX files are allowed");
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setUploadError("File size must be less than 10MB");
      return;
    }

    setResumeFile(file);
    setUploadError(null);
    setResumeId(null);
    setIsUploading(true);

    try {
      const result = await uploadResume(file);
      setResumeId(result.file_id);
      toast.success("Resume uploaded successfully");
    } catch (error) {
      if (error instanceof AxiosError) {
        const msg =
          typeof error.response?.data === "object" && error.response?.data
            ? JSON.stringify(error.response.data)
            : "Failed to upload resume";
        setUploadError(msg);
      } else {
        setUploadError("Failed to upload resume");
      }
      setResumeFile(null);
    } finally {
      setIsUploading(false);
    }
  }

  async function handleResumeChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    await processResumeFile(file);
  }

  function handleDragOver(e: React.DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setIsDraggingOver(true);
  }

  function handleDragLeave(e: React.DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setIsDraggingOver(false);
  }

  async function handleDrop(e: React.DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setIsDraggingOver(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    await processResumeFile(file);
  }

  function setTextAnswer(questionId: string, value: string) {
    setTextAnswers((prev) => ({ ...prev, [questionId]: value }));
  }

  function toggleMcqChoice(questionId: string, choice: string) {
    setMcqAnswers((prev) => {
      const current = prev[questionId] ?? [];
      const next = current.includes(choice)
        ? current.filter((c) => c !== choice)
        : [...current, choice];
      return { ...prev, [questionId]: next };
    });
  }

  function setMcqSingleChoice(questionId: string, choice: string) {
    setMcqAnswers((prev) => ({ ...prev, [questionId]: [choice] }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!profile) return;

    // Build answers array
    const answers: JobApplicationCreate["answers"] = [];
    for (const q of profile.questions ?? []) {
      if (!q.id) continue;

      if (q.question_type === "text") {
        const text = textAnswers[q.id] ?? "";
        if (q.is_required && !text.trim()) {
          toast.error(`Please answer: "${q.text}"`);
          return;
        }
        answers.push({ question: q.id, answer_text: text || null });
      } else {
        // mcq or mcq_single
        const choices = mcqAnswers[q.id] ?? [];
        if (q.is_required && choices.length === 0) {
          toast.error(`Please answer: "${q.text}"`);
          return;
        }
        answers.push({
          question: q.id,
          selected_choices: choices,
        });
      }
    }

    const payload: JobApplicationCreate = {
      job_profile: jobId,
      first_name: firstName,
      last_name: lastName,
      email,
      phone: dialCode ? `+${dialCode}${phoneNumber}` : phoneNumber,
      address: {
        line1,
        line2: line2 || undefined,
        city: cityName || "N/A",
        province_state: stateCode || "N/A",
        postal_code: postalCode,
        country: countryCode,
      },
      answers,
      resume_id: resumeId ?? undefined,
    };

    setIsSubmitting(true);
    try {
      await submitApplication(payload);
      setIsSubmitted(true);
      toast.success("Application submitted successfully!");
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
          toast.error(messages || "Failed to submit application");
        } else {
          toast.error("Failed to submit application");
        }
      } else {
        toast.error("Failed to submit application");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  // ─── Loading ─────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="mx-auto w-full max-w-3xl px-6 py-8 space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-64 w-full rounded-lg" />
      </div>
    );
  }

  // ─── Not found ───────────────────────────────────────────────────────────
  if (notFound || !profile) {
    return (
      <div className="mx-auto w-full max-w-3xl px-6 py-16 text-center">
        <XCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        <h1 className="text-2xl font-semibold mb-2">Job Profile Not Found</h1>
        <p className="text-muted-foreground">
          This job posting may have been removed or is no longer accepting
          applications.
        </p>
      </div>
    );
  }

  // ─── Success ─────────────────────────────────────────────────────────────
  if (isSubmitted) {
    return (
      <div className="mx-auto w-full max-w-3xl px-6 py-16 text-center">
        <CheckCircle2 className="mx-auto h-12 w-12 text-green-500 mb-4" />
        <h1 className="text-2xl font-semibold mb-2">Application Submitted!</h1>
        <p className="text-muted-foreground">
          Thank you for applying to{" "}
          <span className="font-medium text-foreground">{profile.title}</span>.
          We&apos;ll be in touch if your profile is a match.
        </p>
      </div>
    );
  }

  // ─── Main view ───────────────────────────────────────────────────────────
  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-8">
      {/* Job Details Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold mb-1">{profile.title}</h1>
        <p className="text-muted-foreground text-sm mb-3">
          {(profile.organization as { name?: string })?.name}
        </p>

        <div className="flex flex-wrap gap-2 mb-4">
          {profile.category && (
            <Badge variant="secondary">
              <Briefcase className="mr-1 h-3 w-3" />
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
      </div>

      {/* Job Description */}
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
      {((profile.qualifications ?? []) as Qualification[]).length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <List className="h-4 w-4" />
              Qualifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <QualificationsDisplay
              qualifications={(profile.qualifications ?? []) as Qualification[]}
              showCategoryBadge={false}
            />
          </CardContent>
        </Card>
      )}

      <Separator className="my-8" />

      {/* Application Form */}
      <form onSubmit={handleSubmit}>
        <h2 className="text-xl font-semibold mb-6">Apply for this position</h2>

        {/* Personal Information */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">Personal Information</CardTitle>
            <CardDescription>Your contact details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstName">
                  First Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="firstName"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                  placeholder="John"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="lastName">
                  Last Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="lastName"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                  placeholder="Doe"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="email">
                  Email <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="john@example.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">
                  Phone <span className="text-destructive">*</span>
                </Label>
                <PhoneInput
                  countries={countryOptions}
                  dialCode={dialCode}
                  number={phoneNumber}
                  onDialCodeChange={setDialCode}
                  onNumberChange={setPhoneNumber}
                  required
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Address */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <MapPin className="h-4 w-4" />
              Address
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Country */}
            <div className="space-y-2">
              <Label>
                Country <span className="text-destructive">*</span>
              </Label>
              <LocationCombobox
                placeholder="Select country..."
                value={countryCode}
                options={countryOptions.map((c) => ({
                  value: c.iso2,
                  label: c.name,
                }))}
                onChange={(val) => {
                  setCountryCode(val);
                  setStateCode("");
                  setCityName("");
                }}
              />
            </div>

            {/* Province / State */}
            <div className="space-y-2">
              <Label>Province / State</Label>
              <LocationCombobox
                placeholder={
                  countryCode
                    ? "Select province/state..."
                    : "Select a country first"
                }
                disabled={!countryCode}
                value={stateCode}
                options={stateOptions.map((s) => ({
                  value: s.iso2,
                  label: s.name,
                }))}
                onChange={(val) => {
                  setStateCode(val);
                  setCityName("");
                }}
              />
            </div>

            {/* City */}
            <div className="space-y-2">
              <Label>City</Label>
              <LocationCombobox
                placeholder={
                  stateCode ? "Select city..." : "Select a province/state first"
                }
                disabled={!stateCode}
                value={cityName}
                options={cityOptions.map((c) => ({
                  value: c.name,
                  label: c.name,
                }))}
                onChange={setCityName}
                allowFreeform
              />
            </div>

            {/* Line 1 */}
            <div className="space-y-2">
              <Label htmlFor="line1">
                Address Line 1 <span className="text-destructive">*</span>
              </Label>
              <Input
                id="line1"
                value={line1}
                onChange={(e) => setLine1(e.target.value)}
                required
                placeholder="123 Main St"
              />
            </div>

            {/* Line 2 */}
            <div className="space-y-2">
              <Label htmlFor="line2">Address Line 2</Label>
              <Input
                id="line2"
                value={line2}
                onChange={(e) => setLine2(e.target.value)}
                placeholder="Apt 4B"
              />
            </div>

            {/* Postal Code */}
            <div className="space-y-2">
              <Label htmlFor="postalCode">
                Postal Code <span className="text-destructive">*</span>
              </Label>
              <Input
                id="postalCode"
                value={postalCode}
                onChange={(e) => setPostalCode(e.target.value)}
                required
              />
            </div>
          </CardContent>
        </Card>

        {/* Questions */}
        {profile.questions && profile.questions.length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-base">Application Questions</CardTitle>
              <CardDescription>
                Please answer the following questions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {profile.questions.map((q: Question, i: number) => (
                <div key={q.id ?? i}>
                  {i > 0 && <Separator className="mb-6" />}
                  <QuestionField
                    question={q}
                    textValue={textAnswers[q.id ?? ""] ?? ""}
                    mcqValues={mcqAnswers[q.id ?? ""] ?? []}
                    onTextChange={(v) => setTextAnswer(q.id ?? "", v)}
                    onMcqToggle={(c) => toggleMcqChoice(q.id ?? "", c)}
                    onMcqSingleSelect={(c) => setMcqSingleChoice(q.id ?? "", c)}
                  />
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Resume Upload */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Upload className="h-4 w-4" />
              Resume
              <span className="text-destructive">*</span>
            </CardTitle>
            <CardDescription>
              Upload your resume (PDF, DOC, DOCX — max 10MB)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <label
                htmlFor="resume"
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-8 text-center cursor-pointer transition-colors ${
                  isDraggingOver
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-muted-foreground/30 text-muted-foreground hover:border-muted-foreground/50"
                }`}
              >
                {isDraggingOver ? (
                  <>
                    <Upload className="h-8 w-8" />
                    <span className="text-sm font-medium">Drop file here</span>
                  </>
                ) : isUploading ? (
                  <>
                    <Loader2 className="h-8 w-8 animate-spin" />
                    <span className="text-sm">Uploading resume...</span>
                  </>
                ) : resumeFile && resumeId ? (
                  <>
                    <FileText className="h-8 w-8 text-green-600" />
                    <span className="text-sm text-green-600 font-medium">
                      {resumeFile.name}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Click or drag to replace
                    </span>
                  </>
                ) : (
                  <>
                    <Upload className="h-8 w-8" />
                    <span className="text-sm font-medium">
                      Click to upload or drag and drop
                    </span>
                    <span className="text-xs">PDF, DOC, DOCX — max 10MB</span>
                  </>
                )}
                <input
                  id="resume"
                  type="file"
                  accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={handleResumeChange}
                  disabled={isUploading}
                  className="sr-only"
                  required
                />
              </label>
              {uploadError && (
                <p className="text-sm text-destructive">{uploadError}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Submit */}
        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={isSubmitting || isUploading}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Submitting...
            </>
          ) : isUploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Waiting for resume upload...
            </>
          ) : (
            "Submit Application"
          )}
        </Button>
      </form>
    </div>
  );
}
