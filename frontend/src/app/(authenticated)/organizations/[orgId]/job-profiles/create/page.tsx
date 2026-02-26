"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import {
  listJobCategories,
  listExperienceLevels,
  listAiScreeningConfigs,
  createJobProfile,
} from "@/lib/api";
import type {
  JobCategory,
  ExperienceLevel,
  AiScreeningConfiguration,
} from "@/lib/client";
import {
  JobProfileForm,
  type JobProfileFormValues,
} from "@/components/job-profile-form";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft } from "lucide-react";

export default function CreateJobProfilePage({
  params,
}: {
  params: Promise<{ orgId: string }>;
}) {
  const { orgId } = use(params);
  const router = useRouter();

  const [categories, setCategories] = useState<JobCategory[]>([]);
  const [experienceLevels, setExperienceLevels] = useState<ExperienceLevel[]>(
    [],
  );
  const [aiScreeningConfigs, setAiScreeningConfigs] = useState<
    AiScreeningConfiguration[]
  >([]);
  const [isLoadingRef, setIsLoadingRef] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([
      listJobCategories(),
      listExperienceLevels(),
      listAiScreeningConfigs(),
    ])
      .then(([cats, levels, configs]) => {
        setCategories(cats ?? []);
        setExperienceLevels(levels ?? []);
        setAiScreeningConfigs(configs ?? []);
      })
      .catch(() => toast.error("Failed to load reference data"))
      .finally(() => setIsLoadingRef(false));
  }, []);

  async function handleSubmit(values: JobProfileFormValues) {
    setIsSubmitting(true);
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const payload: any = {
        ...values,
        organization: orgId,
        // Filter out blank requirements
        requirements: values.requirements.filter((r) => r.trim()),
        // Normalize questions
        questions: values.questions.map((q, i) => ({
          ...q,
          order: i,
          choices: q.choices.filter((c) => c.trim()),
        })),
      };
      delete payload.is_active; // not sent on create

      const created = await createJobProfile(payload);
      toast.success("Job profile created successfully");
      if (created?.id) {
        router.push(`/organizations/${orgId}/job-profiles/${created.id}`);
      } else {
        router.push(`/organizations/${orgId}/job-profiles`);
      }
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
          toast.error(messages || "Failed to create job profile");
        } else {
          toast.error("Failed to create job profile");
        }
      } else {
        toast.error("Failed to create job profile");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="container max-w-3xl px-6 py-8">
      <div className="mb-6">
        <Link
          href={`/organizations/${orgId}/job-profiles`}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Job Profiles
        </Link>
        <h1 className="font-heading text-2xl font-semibold">New Job Profile</h1>
        <p className="text-muted-foreground">
          Create a new job profile to start receiving applications.
        </p>
      </div>

      {isLoadingRef ? (
        <div className="space-y-6">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-48 w-full rounded-lg" />
          ))}
        </div>
      ) : (
        <JobProfileForm
          categories={categories}
          experienceLevels={experienceLevels}
          aiScreeningConfigs={aiScreeningConfigs}
          onSubmit={handleSubmit}
          submitLabel="Create Job Profile"
          isSubmitting={isSubmitting}
          showIsActive={false}
        />
      )}
    </div>
  );
}
