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
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const invitationToken = searchParams.get("token") || "";
  const invitationEmail = searchParams.get("email") || "";

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
      router.push("/organizations");
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
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-heading">Create account</CardTitle>
        <CardDescription>
          {invitationToken
            ? "Complete your registration to join the organization"
            : "Sign up for a Talentika account"}
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={(e) => updateField("email", e.target.value)}
              required
              autoComplete="email"
              disabled={!!invitationEmail}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              type="text"
              placeholder="johndoe"
              value={form.username}
              onChange={(e) => updateField("username", e.target.value)}
              required
              autoComplete="username"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="first_name">First name</Label>
              <Input
                id="first_name"
                type="text"
                placeholder="John"
                value={form.first_name}
                onChange={(e) => updateField("first_name", e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="last_name">Last name</Label>
              <Input
                id="last_name"
                type="text"
                placeholder="Doe"
                value={form.last_name}
                onChange={(e) => updateField("last_name", e.target.value)}
                required
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Create a password"
              value={form.password}
              onChange={(e) => updateField("password", e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password_confirm">Confirm password</Label>
            <Input
              id="password_confirm"
              type="password"
              placeholder="Confirm your password"
              value={form.password_confirm}
              onChange={(e) => updateField("password_confirm", e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create account
          </Button>
          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
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
