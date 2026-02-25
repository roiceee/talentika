"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/auth-context";
import { updateUserProfile } from "@/lib/api";
import { toast } from "sonner";
import { AxiosError } from "axios";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Loader2, Pencil } from "lucide-react";

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    username: user?.username || "",
    first_name: user?.first_name || "",
    last_name: user?.last_name || "",
  });

  if (!user) return null;

  const initials =
    `${user.first_name?.[0] || ""}${user.last_name?.[0] || ""}`.toUpperCase() ||
    user.email?.[0]?.toUpperCase() ||
    "?";

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setIsSaving(true);
    try {
      await updateUserProfile(form);
      await refreshUser();
      toast.success("Profile updated");
      setEditing(false);
    } catch (error) {
      if (error instanceof AxiosError) {
        const data = error.response?.data;
        if (data && typeof data === "object") {
          const messages = Object.entries(data)
            .map(([key, val]) => {
              const msg = Array.isArray(val) ? val.join(", ") : String(val);
              return `${key}: ${msg}`;
            })
            .join("\n");
          toast.error(messages || "Failed to update profile");
        } else {
          toast.error("Failed to update profile");
        }
      }
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="container max-w-2xl px-6 py-8">
      <h1 className="mb-6 font-heading text-2xl font-semibold">Profile</h1>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="bg-primary text-primary-foreground text-xl">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div>
              <CardTitle>
                {user.first_name} {user.last_name}
              </CardTitle>
              <CardDescription>{user.email}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <Separator />
        <CardContent className="pt-6">
          {editing ? (
            <form onSubmit={handleSave} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={form.username}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, username: e.target.value }))
                  }
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="first_name">First name</Label>
                  <Input
                    id="first_name"
                    value={form.first_name}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        first_name: e.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="last_name">Last name</Label>
                  <Input
                    id="last_name"
                    value={form.last_name}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        last_name: e.target.value,
                      }))
                    }
                    required
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={isSaving}>
                  {isSaving && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Save changes
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setEditing(false);
                    setForm({
                      username: user.username ?? "",
                      first_name: user.first_name ?? "",
                      last_name: user.last_name ?? "",
                    });
                  }}
                >
                  Cancel
                </Button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Username
                  </p>
                  <p>{user.username}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Email
                  </p>
                  <p>{user.email}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    First name
                  </p>
                  <p>{user.first_name}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Last name
                  </p>
                  <p>{user.last_name}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Member since
                  </p>
                  <p>
                    {user.date_joined
                      ? new Date(user.date_joined).toLocaleDateString()
                      : "—"}
                  </p>
                </div>
              </div>
              <Button variant="outline" onClick={() => setEditing(true)}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit profile
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
