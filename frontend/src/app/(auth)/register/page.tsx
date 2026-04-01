"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/contexts/auth-context";
import { toast } from "sonner";
import { AxiosError } from "axios";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const invitationToken = searchParams.get("token") || "";
  const invitationEmail = searchParams.get("email") || "";
  const redirect = searchParams.get("redirect") || "";

  const { register } = useAuth();
  const [form, setForm] = useState({
    email: invitationEmail,
    username: "",
    first_name: "",
    last_name: "",
    password: "",
    password_confirm: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateField(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (form.password !== form.password_confirm) {
      toast.error("Passwords don't match");
      return;
    }

    setIsSubmitting(true);

    try {
      await register({
        ...form,
        ...(invitationToken ? { invitation_token: invitationToken } : {}),
      });
      toast.success("Account created successfully!");
      // If registration included an invitation token, the user was
      // automatically joined to the org on the backend — go to orgs.
      // If there's an explicit redirect, honour it.
      router.push(redirect || "/organizations");
    } catch (error) {
      if (error instanceof AxiosError) {
        const data = error.response?.data;
        if (data && typeof data === "object") {
          // Django returns field-level errors as { field: [messages] }
          const messages = Object.entries(data)
            .map(([key, val]) => {
              const msg = Array.isArray(val) ? val.join(", ") : String(val);
              return `${key}: ${msg}`;
            })
            .join("\n");
          toast.error(messages || "Registration failed");
        } else {
          toast.error("Registration failed. Please try again.");
        }
      } else {
        toast.error("Something went wrong. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <div className="mb-8">
        <h1 className="font-heading text-2xl text-foreground mb-1">Create account</h1>
        <p className="text-muted-foreground text-sm">
          {invitationToken
            ? "Complete your registration to join the organization"
            : "Sign up for a Talentika account"}
        </p>
      </div>
      <Card className="shadow-md border-border/60">
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 pt-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                required
                autoComplete="email"
                disabled={!!invitationEmail}
                className="h-10"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="johndoe"
                value={form.username}
                onChange={(e) => updateField("username", e.target.value)}
                required
                autoComplete="username"
                className="h-10"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name" className="text-sm font-medium">First name</Label>
                <Input
                  id="first_name"
                  type="text"
                  placeholder="John"
                  value={form.first_name}
                  onChange={(e) => updateField("first_name", e.target.value)}
                  required
                  className="h-10"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name" className="text-sm font-medium">Last name</Label>
                <Input
                  id="last_name"
                  type="text"
                  placeholder="Doe"
                  value={form.last_name}
                  onChange={(e) => updateField("last_name", e.target.value)}
                  required
                  className="h-10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">Password</Label>
              <PasswordInput
                id="password"
                placeholder="Create a password"
                value={form.password}
                onChange={(e) => updateField("password", e.target.value)}
                required
                autoComplete="new-password"
                className="h-10"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password_confirm" className="text-sm font-medium">Confirm password</Label>
              <PasswordInput
                id="password_confirm"
                placeholder="Confirm your password"
                value={form.password_confirm}
                onChange={(e) => updateField("password_confirm", e.target.value)}
                required
                autoComplete="new-password"
                className="h-10"
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4 pb-6">
            <Button type="submit" className="w-full h-10 font-semibold" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create account
            </Button>
            <p className="text-sm text-muted-foreground text-center">
              Already have an account?{" "}
              <Link
                href={
                  invitationToken
                    ? `/login?redirect=${encodeURIComponent(`/invite/accept?token=${invitationToken}`)}`
                    : redirect
                      ? `/login?redirect=${encodeURIComponent(redirect)}`
                      : "/login"
                }
                className="text-primary hover:underline font-medium"
              >
                Sign in
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </>
  );
}

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <Card>
          <CardContent className="py-12">
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      }
    >
      <RegisterForm />
    </Suspense>
  );
}
