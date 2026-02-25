"use client";

import { useAuth } from "@/contexts/auth-context";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppNavbar } from "@/components/app-navbar";
import { Skeleton } from "@/components/ui/skeleton";

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col">
        <div className="border-b px-6 py-4">
          <Skeleton className="h-8 w-32" />
        </div>
        <div className="flex-1 p-6">
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col">
      <AppNavbar />
      <main className="flex-1">{children}</main>
    </div>
  );
}
