"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Dashboard page — smart landing page after login.
 *
 * - If the user has a default organization → redirect to job profiles.
 * - Otherwise → redirect to organizations page to pick one.
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
      router.replace("/job-profiles");
      return;
    }

    router.replace("/organizations");
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
