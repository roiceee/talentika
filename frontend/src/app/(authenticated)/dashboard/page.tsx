"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { listOrganizations } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Dashboard page — smart landing page after login.
 *
 * - If the user has a default organization → redirect to its job profiles.
 * - If no default organization → pick the first org in the list and redirect there.
 * - If the user has no organizations at all → redirect to /organizations.
 */
export default function DashboardPage() {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }

    if (user?.default_organization) {
      router.replace(
        `/organizations/${user.default_organization}/job-profiles`,
      );
      return;
    }

    // No default — use the first org the user belongs to.
    listOrganizations()
      .then((orgs) => {
        const first = orgs?.[0];
        if (first) {
          router.replace(`/organizations/${first.id}/job-profiles`);
        } else {
          router.replace("/organizations");
        }
      })
      .catch(() => {
        router.replace("/organizations");
      });
  }, [user, isLoading, isAuthenticated, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="space-y-4 text-center">
        <Skeleton className="mx-auto h-8 w-48" />
        <Skeleton className="mx-auto h-4 w-32" />
      </div>
    </div>
  );
}
