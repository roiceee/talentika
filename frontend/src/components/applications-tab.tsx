"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import { listJobApplications } from "@/lib/api";
import type { JobApplicationDetail } from "@/lib/client";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Mail, Phone, FileText, User } from "lucide-react";

const STATUS_CONFIG: Record<
  string,
  {
    label: string;
    variant: "default" | "secondary" | "outline" | "destructive";
    className?: string;
  }
> = {
  to_be_reviewed: { label: "To Be Reviewed", variant: "secondary" },
  reviewed: { label: "Reviewed", variant: "default" },
  shortlisted: {
    label: "Shortlisted",
    variant: "default",
    className: "bg-emerald-600 text-white hover:bg-emerald-700",
  },
  rejected: { label: "Rejected", variant: "destructive" },
};

interface ApplicationsTabProps {
  orgId: string;
  jobProfileId: string;
}

export function ApplicationsTab({ orgId, jobProfileId }: ApplicationsTabProps) {
  const router = useRouter();
  const [applications, setApplications] = useState<JobApplicationDetail[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchApplications = useCallback(async () => {
    try {
      const data = await listJobApplications(orgId, jobProfileId);
      setApplications(data);
    } catch (error) {
      if (error instanceof AxiosError && error.response?.status === 403) {
        toast.error("You don't have permission to view applications");
      } else {
        toast.error("Failed to load applications");
      }
    } finally {
      setIsLoading(false);
    }
  }, [orgId, jobProfileId]);

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  if (applications.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <FileText className="h-12 w-12 text-muted-foreground/40 mb-4" />
          <h3 className="text-lg font-medium mb-1">No applications yet</h3>
          <p className="text-sm text-muted-foreground">
            Applications will appear here once candidates apply for this job
            profile.
          </p>
        </CardContent>
      </Card>
    );
  }

  // ─── List view ───────────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {applications.length} application{applications.length !== 1 && "s"}
        </p>
      </div>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Applicant</TableHead>
              <TableHead>Contact</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Submitted</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {applications.map((app) => {
              const statusConfig =
                STATUS_CONFIG[app.status ?? "to_be_reviewed"];
              return (
                <TableRow
                  key={app.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() =>
                    router.push(
                      `/job-profiles/${jobProfileId}/applications/${app.id}`,
                    )
                  }
                >
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                        <User className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">
                          {app.first_name} {app.last_name}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                        <Mail className="h-3.5 w-3.5" />
                        {app.email}
                      </div>
                      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                        <Phone className="h-3.5 w-3.5" />
                        {app.phone}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={statusConfig?.variant ?? "secondary"}
                      className={statusConfig?.className}
                    >
                      {statusConfig?.label ?? app.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {app.submitted_at
                      ? new Date(app.submitted_at).toLocaleDateString(
                          undefined,
                          {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                          },
                        )
                      : "—"}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
