"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { toast } from "sonner";
import type { OrganizationListItem, OrganizationCreateData } from "@/types";
import { listOrganizations, createOrganization } from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";
import { setDefaultOrganization } from "@/lib/api";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Building2,
  Plus,
  Users,
  Loader2,
  Star,
  Search,
  ArrowUpDown,
  X,
  Calendar,
  Check,
} from "lucide-react";

const STATUS_LABELS: Record<string, string> = {
  PENDING: "Pending",
  APPROVED: "Approved",
  REJECTED: "Rejected",
  SUSPENDED: "Suspended",
};

const STATUS_VARIANTS: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  APPROVED: "default",
  PENDING: "secondary",
  REJECTED: "destructive",
  SUSPENDED: "outline",
};

export default function OrganizationsPage() {
  const { user, refreshUser } = useAuth();
  const [settingDefaultId, setSettingDefaultId] = useState<string | null>(null);
  const [orgs, setOrgs] = useState<OrganizationListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newOrg, setNewOrg] = useState<OrganizationCreateData>({
    name: "",
    description: "",
  });

  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [sort, setSort] = useState("newest");

  async function fetchOrgs() {
    try {
      const data = await listOrganizations();
      setOrgs(data ?? []);
    } catch (error) {
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

  async function handleSetDefault(e: React.MouseEvent, orgId: string) {
    e.preventDefault();
    e.stopPropagation();
    setSettingDefaultId(orgId);
    try {
      const isAlreadyDefault = user?.default_organization === orgId;
      await setDefaultOrganization(isAlreadyDefault ? null : orgId);
      await refreshUser();
      toast.success(
        isAlreadyDefault
          ? "Default organization cleared"
          : "Default organization updated",
      );
    } catch {
      toast.error("Failed to update default organization");
    } finally {
      setSettingDefaultId(null);
    }
  }

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

  const filtered = useMemo(() => {
    let result = [...orgs];

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (o) =>
          o.name.toLowerCase().includes(q) ||
          o.description?.toLowerCase().includes(q),
      );
    }

    if (filterStatus !== "all") {
      result = result.filter((o) => o.status === filterStatus);
    }

    result.sort((a, b) => {
      if (sort === "newest")
        return (
          new Date(b.created_at ?? 0).getTime() -
          new Date(a.created_at ?? 0).getTime()
        );
      if (sort === "oldest")
        return (
          new Date(a.created_at ?? 0).getTime() -
          new Date(b.created_at ?? 0).getTime()
        );
      if (sort === "az") return a.name.localeCompare(b.name);
      if (sort === "za") return b.name.localeCompare(a.name);
      if (sort === "members")
        return (b.member_count ?? 0) - (a.member_count ?? 0);
      return 0;
    });

    return result;
  }, [orgs, search, filterStatus, sort]);

  const hasFilters = search.trim() || filterStatus !== "all";

  function clearFilters() {
    setSearch("");
    setFilterStatus("all");
  }

  return (
    <div className="w-full py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-2xl font-semibold">Organizations</h1>
          <p className="text-muted-foreground text-sm mt-0.5">
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
        <>
          <div className="flex gap-3">
            <Skeleton className="h-9 flex-1" />
            <Skeleton className="h-9 w-36" />
            <Skeleton className="h-9 w-36" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-44 w-full" />
            ))}
          </div>
        </>
      ) : orgs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <Building2 className="h-7 w-7 text-primary" />
            </div>
            <h3 className="mb-2 font-heading text-lg font-semibold">
              No organizations yet
            </h3>
            <p className="mb-4 text-sm text-muted-foreground text-center max-w-md">
              Create your first organization to get started. You need an
              organization before you can create job profiles and manage
              applications.
            </p>
            <Button onClick={() => setDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create organization
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-48">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
              <Input
                placeholder="Search by name or description…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8"
              />
            </div>

            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={sort} onValueChange={setSort}>
              <SelectTrigger className="w-40">
                <ArrowUpDown className="h-3.5 w-3.5 mr-1.5 text-muted-foreground" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="newest">Newest first</SelectItem>
                <SelectItem value="oldest">Oldest first</SelectItem>
                <SelectItem value="az">Name A–Z</SelectItem>
                <SelectItem value="za">Name Z–A</SelectItem>
                <SelectItem value="members">Most members</SelectItem>
              </SelectContent>
            </Select>

            {hasFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
                className="gap-1.5 text-muted-foreground"
              >
                <X className="h-3.5 w-3.5" />
                Clear
              </Button>
            )}
          </div>

          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Search className="h-10 w-10 text-muted-foreground/40 mb-3" />
              <p className="font-medium">No organizations match your filters</p>
              <p className="text-sm text-muted-foreground mt-1">
                Try adjusting your search or filters.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={clearFilters}
                className="mt-4"
              >
                Clear filters
              </Button>
            </div>
          ) : (
            <>
              <p className="text-sm text-muted-foreground">
                {filtered.length} of {orgs.length} organization
                {orgs.length !== 1 ? "s" : ""}
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filtered.map((org) => (
                  <Link
                    key={org.id}
                    href={`/organizations/${org.id}`}
                    className="block group"
                  >
                    <Card className="h-full flex flex-col transition-all duration-150 hover:shadow-md hover:border-primary/30">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0 flex-1">
                            <CardTitle className="text-base leading-snug group-hover:text-primary transition-colors truncate">
                              {org.name}
                            </CardTitle>
                          </div>
                          <div className="flex items-center gap-1.5 shrink-0">
                            {org.status && (
                              <Badge
                                variant={
                                  STATUS_VARIANTS[org.status] ?? "secondary"
                                }
                                className="text-xs font-normal"
                              >
                                {STATUS_LABELS[org.status] ?? org.status}
                              </Badge>
                            )}
                            {user?.default_organization === org.id && (
                              <Badge
                                variant="outline"
                                className="bg-yellow-50 text-yellow-700 border-yellow-300 text-xs font-normal"
                              >
                                <Star className="mr-1 h-3 w-3 fill-yellow-400" />
                                Default
                              </Badge>
                            )}
                          </div>
                        </div>
                        {org.description && (
                          <CardDescription className="line-clamp-2 mt-1">
                            {org.description}
                          </CardDescription>
                        )}
                      </CardHeader>

                      <CardContent className="flex-1 pb-3">
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1.5">
                            <Users className="h-3.5 w-3.5" />
                            {org.member_count ?? 0} member
                            {(org.member_count ?? 0) !== 1 ? "s" : ""}
                          </span>
                        </div>
                      </CardContent>

                      <CardFooter className="pt-0 pb-4 flex items-center justify-between">
                        {org.created_at && (
                          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                            <Calendar className="h-3 w-3" />
                            <span>
                              {new Date(org.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        )}
                        <Button
                          variant={
                            user?.default_organization === org.id
                              ? "secondary"
                              : "outline"
                          }
                          size="sm"
                          className="h-7 text-xs ml-auto"
                          onClick={(e) => handleSetDefault(e, org.id!)}
                          disabled={settingDefaultId === org.id}
                        >
                          {settingDefaultId === org.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : user?.default_organization === org.id ? (
                            <Check className="h-3 w-3" />
                          ) : (
                            <Star className="h-3 w-3" />
                          )}
                          {user?.default_organization === org.id
                            ? "Selected"
                            : "Select org"}
                        </Button>
                      </CardFooter>
                    </Card>
                  </Link>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
