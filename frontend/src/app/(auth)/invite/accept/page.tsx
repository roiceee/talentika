"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/contexts/auth-context";
import { validateInvitation, acceptInvitation } from "@/lib/api";
import { toast } from "sonner";
import { AxiosError } from "axios";
import type { InvitationValidationResult } from "@/types";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Loader2,
  Building2,
  CheckCircle,
  XCircle,
  LogIn,
  UserPlus,
} from "lucide-react";

function InviteAcceptContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const {
    isAuthenticated,
    isLoading: authLoading,
    user,
    refreshUser,
  } = useAuth();
  const token = searchParams.get("token") || "";

  const [invitation, setInvitation] =
    useState<InvitationValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(true);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isAccepting, setIsAccepting] = useState(false);
  const [accepted, setAccepted] = useState(false);

  useEffect(() => {
    if (!token) {
      setValidationError("No invitation token provided");
      setIsValidating(false);
      return;
    }

    async function validate() {
      try {
        const result = await validateInvitation(token);
        setInvitation(result);
      } catch (error) {
        if (error instanceof AxiosError) {
          setValidationError(
            error.response?.data?.error || "Invalid invitation",
          );
        } else {
          setValidationError("Failed to validate invitation");
        }
      } finally {
        setIsValidating(false);
      }
    }

    validate();
  }, [token]);

  async function handleAccept() {
    setIsAccepting(true);
    try {
      await acceptInvitation(token);
      await refreshUser();
      setAccepted(true);
      toast.success("Successfully joined the organization!");
    } catch (error) {
      if (error instanceof AxiosError) {
        toast.error(
          error.response?.data?.error || "Failed to accept invitation",
        );
      }
    } finally {
      setIsAccepting(false);
    }
  }

  if (isValidating || authLoading) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="flex flex-col items-center gap-4">
            <Skeleton className="h-12 w-12 rounded-full" />
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (validationError) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <XCircle className="mb-4 h-12 w-12 text-destructive" />
          <h2 className="mb-2 font-heading text-xl font-semibold">
            Invalid invitation
          </h2>
          <p className="mb-6 text-sm text-muted-foreground">
            {validationError}
          </p>
          <Link href="/login">
            <Button variant="outline">Go to sign in</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (accepted) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <CheckCircle className="mb-4 h-12 w-12 text-green-600" />
          <h2 className="mb-2 font-heading text-xl font-semibold">
            Welcome to {invitation?.organization_name}!
          </h2>
          <p className="mb-6 text-sm text-muted-foreground">
            You&apos;ve successfully joined the organization.
          </p>
          <Button
            onClick={() =>
              router.push(`/organizations/${invitation?.organization_id}`)
            }
          >
            Go to organization
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!invitation) return null;

  // Not authenticated — show sign in / register options
  if (!isAuthenticated) {
    return (
      <Card>
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            <Building2 className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="font-heading">
            You&apos;re invited to join
          </CardTitle>
          <CardDescription className="text-lg font-semibold text-foreground">
            {invitation.organization_name}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-center text-sm text-muted-foreground">
          <p>
            Invited by <strong>{invitation.invited_by}</strong> as{" "}
            <Badge variant="secondary">{invitation.role}</Badge>
          </p>
          <p>
            This invitation is for <strong>{invitation.email}</strong>
          </p>
        </CardContent>
        <CardFooter className="flex flex-col gap-3">
          <Link
            href={`/login?redirect=${encodeURIComponent(`/invite/accept?token=${token}`)}`}
            className="w-full"
          >
            <Button className="w-full">
              <LogIn className="mr-2 h-4 w-4" />
              Sign in to accept
            </Button>
          </Link>
          <Link
            href={`/register?token=${token}&email=${encodeURIComponent(invitation.email ?? "")}`}
            className="w-full"
          >
            <Button variant="outline" className="w-full">
              <UserPlus className="mr-2 h-4 w-4" />
              Create account
            </Button>
          </Link>
        </CardFooter>
      </Card>
    );
  }

  // Authenticated — show accept button
  const emailMatch =
    user?.email?.toLowerCase() === invitation.email?.toLowerCase();

  return (
    <Card>
      <CardHeader className="text-center">
        <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <Building2 className="h-6 w-6 text-primary" />
        </div>
        <CardTitle className="font-heading">
          Join {invitation.organization_name}
        </CardTitle>
        <CardDescription>
          You&apos;ve been invited by {invitation.invited_by}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-center text-sm">
        <div className="flex justify-center gap-2">
          <Badge variant="secondary">{invitation.role}</Badge>
        </div>
        {!emailMatch && (
          <p className="text-destructive">
            This invitation is for <strong>{invitation.email}</strong>, but
            you&apos;re signed in as <strong>{user?.email}</strong>. Please sign
            in with the correct account.
          </p>
        )}
      </CardContent>
      <CardFooter>
        <Button
          className="w-full"
          onClick={handleAccept}
          disabled={isAccepting || !emailMatch}
        >
          {isAccepting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Accept invitation
        </Button>
      </CardFooter>
    </Card>
  );
}

export default function InviteAcceptPage() {
  return (
    <Suspense
      fallback={
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center gap-4">
              <Skeleton className="h-12 w-12 rounded-full" />
              <Skeleton className="h-6 w-48" />
            </div>
          </CardContent>
        </Card>
      }
    >
      <InviteAcceptContent />
    </Suspense>
  );
}
