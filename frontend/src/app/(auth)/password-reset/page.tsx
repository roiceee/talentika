"use client";

import { useState } from "react";
import Link from "next/link";
import { requestPasswordReset } from "@/lib/api";
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
import { Loader2, ArrowLeft, CheckCircle } from "lucide-react";

export default function PasswordResetPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await requestPasswordReset(email);
      setSubmitted(true);
    } catch (error) {
      if (error instanceof AxiosError) {
        toast.error(
          error.response?.data?.error || "Failed to send reset email",
        );
      } else {
        toast.error("Something went wrong");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <CheckCircle className="mb-4 h-12 w-12 text-green-600" />
          <h2 className="mb-2 font-heading text-xl font-semibold">
            Check your email
          </h2>
          <p className="mb-6 text-sm text-muted-foreground">
            If an account with that email exists, we&apos;ve sent a password
            reset link.
          </p>
          <Link href="/login">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to sign in
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-heading">Reset password</CardTitle>
        <CardDescription>
          Enter your email and we&apos;ll send you a reset link
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
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              autoFocus
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Send reset link
          </Button>
          <Link
            href="/login"
            className="text-sm text-muted-foreground hover:underline"
          >
            <ArrowLeft className="mr-1 inline h-3 w-3" />
            Back to sign in
          </Link>
        </CardFooter>
      </form>
    </Card>
  );
}
