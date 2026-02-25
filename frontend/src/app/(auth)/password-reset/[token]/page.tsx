"use client";

import { useState, use } from "react";
import Link from "next/link";
import { confirmPasswordReset } from "@/lib/api";
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
import { Loader2, CheckCircle } from "lucide-react";

export default function PasswordResetConfirmPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = use(params);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      toast.error("Passwords don't match");
      return;
    }

    setIsSubmitting(true);
    try {
      await confirmPasswordReset(token, newPassword, confirmPassword);
      setSuccess(true);
      toast.success("Password reset successfully");
    } catch (error) {
      if (error instanceof AxiosError) {
        const data = error.response?.data;
        if (data?.token) {
          toast.error(Array.isArray(data.token) ? data.token[0] : data.token);
        } else if (data?.new_password) {
          toast.error(
            Array.isArray(data.new_password)
              ? data.new_password[0]
              : data.new_password,
          );
        } else {
          toast.error(data?.error || "Failed to reset password");
        }
      } else {
        toast.error("Something went wrong");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  if (success) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <CheckCircle className="mb-4 h-12 w-12 text-green-600" />
          <h2 className="mb-2 font-heading text-xl font-semibold">
            Password reset!
          </h2>
          <p className="mb-6 text-sm text-muted-foreground">
            Your password has been updated. You can now sign in with your new
            password.
          </p>
          <Link href="/login">
            <Button>Sign in</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-heading">
          Set new password
        </CardTitle>
        <CardDescription>Enter your new password below</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="new_password">New password</Label>
            <Input
              id="new_password"
              type="password"
              placeholder="Enter new password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              autoComplete="new-password"
              autoFocus
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm_password">Confirm password</Label>
            <Input
              id="confirm_password"
              type="password"
              placeholder="Confirm new password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>
        </CardContent>
        <CardFooter>
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Reset password
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
