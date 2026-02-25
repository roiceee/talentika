"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import type { OrganizationListItem, OrganizationCreateData } from "@/types";
import { listOrganizations, createOrganization } from "@/lib/api";
import { AxiosError } from "axios";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Building2, Plus, Users, Loader2 } from "lucide-react";

export default function OrganizationsPage() {
  const [orgs, setOrgs] = useState<OrganizationListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newOrg, setNewOrg] = useState<OrganizationCreateData>({
    name: "",
    description: "",
  });

  async function fetchOrgs() {
    try {
      const data = await listOrganizations();
      setOrgs(data ?? []);
    } catch (error) {
      // 404 means no organizations — that's OK
      if (error instanceof AxiosError && error.response?.status === 404) {
        setOrgs([]);
      } else {
        toast.error("Failed to load organizations");
      }
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    fetchOrgs();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setIsCreating(true);
    try {
      await createOrganization(newOrg);
      toast.success("Organization created");
      setDialogOpen(false);
      setNewOrg({ name: "", description: "" });
      await fetchOrgs();
    } catch (error) {
      if (error instanceof AxiosError) {
        const msg =
          error.response?.data?.name?.[0] ||
          error.response?.data?.error ||
          "Failed to create organization";
        toast.error(msg);
      } else {
        toast.error("Something went wrong");
      }
    } finally {
      setIsCreating(false);
    }
  }

  const statusColor: Record<string, string> = {
    APPROVED: "bg-green-100 text-green-800",
    PENDING: "bg-yellow-100 text-yellow-800",
    REJECTED: "bg-red-100 text-red-800",
    SUSPENDED: "bg-gray-100 text-gray-800",
  };

  return (
    <div className="container max-w-4xl px-6 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-heading text-2xl font-semibold">Organizations</h1>
          <p className="text-muted-foreground">
            Manage your organizations and teams
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New organization
            </Button>
          </DialogTrigger>
          <DialogContent>
            <form onSubmit={handleCreate}>
              <DialogHeader>
                <DialogTitle>Create organization</DialogTitle>
                <DialogDescription>
                  Create a new organization. You will be the admin.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="org-name">Name</Label>
                  <Input
                    id="org-name"
                    placeholder="My Organization"
                    value={newOrg.name}
                    onChange={(e) =>
                      setNewOrg((prev) => ({ ...prev, name: e.target.value }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-desc">Description</Label>
                  <Textarea
                    id="org-desc"
                    placeholder="What is this organization about?"
                    value={newOrg.description || ""}
                    onChange={(e) =>
                      setNewOrg((prev) => ({
                        ...prev,
                        description: e.target.value,
                      }))
                    }
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isCreating}>
                  {isCreating && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Create
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      ) : orgs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Building2 className="mb-4 h-12 w-12 text-muted-foreground" />
            <h3 className="mb-2 font-heading text-lg font-semibold">
              No organizations yet
            </h3>
            <p className="mb-4 text-sm text-muted-foreground">
              Create your first organization or accept an invitation to get
              started.
            </p>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create organization
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {orgs.map((org) => (
            <Link
              key={org.id}
              href={`/organizations/${org.id}`}
              className="block"
            >
              <Card className="transition-colors hover:bg-muted/50">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{org.name}</CardTitle>
                    <Badge
                      variant="outline"
                      className={statusColor[org.status ?? ""] || ""}
                    >
                      {org.status}
                    </Badge>
                  </div>
                  {org.description && (
                    <CardDescription className="line-clamp-2">
                      {org.description}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Users className="h-4 w-4" />
                      {org.member_count} member
                      {org.member_count !== 1 ? "s" : ""}
                    </span>
                    <span>
                      Created{" "}
                      {org.created_at
                        ? new Date(org.created_at).toLocaleDateString()
                        : "—"}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
