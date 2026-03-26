"use client";

import { useEffect, useState, useCallback, use } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { AxiosError } from "axios";
import { useAuth } from "@/contexts/auth-context";
import type {
  Organization,
  OrganizationMembership,
  OrganizationInvitation,
  MemberRole,
} from "@/types";
import {
  getOrganization,
  updateOrganization,
  listMembers,
  removeMember,
  leaveOrganization,
  listInvitations,
  createInvitation,
  cancelInvitation,
  resendInvitation,
  uploadOrgProfilePicture,
  deleteOrgProfilePicture,
  listOrgJobCategories,
  listOrgExperienceLevels,
  createOrgJobCategory,
  createOrgExperienceLevel,
  deleteOrgJobCategory,
  deleteOrgExperienceLevel,
  type OrgRefItem,
} from "@/lib/api";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { AvatarUpload } from "@/components/avatar-upload";
import {
  ArrowLeft,
  Users,
  Mail,
  Loader2,
  Pencil,
  Trash2,
  LogOut,
  Send,
  Check,
  Clock,
  X,
  RotateCw,
  Ban,
  Settings,
  Plus,
  Calendar,
  Building,
} from "lucide-react";
import Link from "next/link";

export default function OrganizationDetailPage({
  params,
}: {
  params: Promise<{ orgId: string }>;
}) {
  const { orgId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();

  const activeTab = searchParams.get("tab") ?? "overview";

  function handleTabChange(tab: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", tab);
    router.replace(`?${params.toString()}`, { scroll: false });
  }
  const [org, setOrg] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrganizationMembership[]>([]);
  const [invitations, setInvitations] = useState<OrganizationInvitation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Current user's role in this org
  const currentMembership = members.find((m) => m.user?.id === user?.id);
  const isAdmin = currentMembership?.role === "ORG_ADMIN";

  const fetchData = useCallback(async () => {
    try {
      const [orgData, membersData] = await Promise.all([
        getOrganization(orgId),
        listMembers(orgId),
      ]);
      setOrg(orgData ?? null);
      setMembers(membersData ?? []);

      // Invitations only if member
      try {
        const invData = await listInvitations(orgId);
        setInvitations(invData ?? []);
      } catch {
        // May not have permission
      }
    } catch (error) {
      if (error instanceof AxiosError) {
        if (error.response?.status === 403) {
          toast.error("You don't have access to this organization");
          router.push("/organizations");
          return;
        }
        if (error.response?.status === 404) {
          toast.error("Organization not found");
          router.push("/organizations");
          return;
        }
      }
      toast.error("Failed to load organization");
    } finally {
      setIsLoading(false);
    }
  }, [orgId, router]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (isLoading) {
    return (
      <div className="w-full py-8 space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!org) return null;

  return (
    <div className="w-full py-8">
      <div className="mb-6">
        <Link
          href="/organizations"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to organizations
        </Link>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <AvatarUpload
              imageUrl={org.profile_picture_url}
              initials={org.name?.[0]?.toUpperCase() || "O"}
              className="h-20 w-20"
              editable={isAdmin}
              onUpload={async (file) => {
                try {
                  await uploadOrgProfilePicture(orgId, file);
                  await fetchData();
                  toast.success("Organization picture updated");
                } catch {
                  toast.error("Failed to upload organization picture");
                  throw new Error("upload failed");
                }
              }}
              onDelete={async () => {
                try {
                  await deleteOrgProfilePicture(orgId);
                  await fetchData();
                  toast.success("Organization picture removed");
                } catch {
                  toast.error("Failed to remove organization picture");
                  throw new Error("delete failed");
                }
              }}
            />
            <div>
              <h1 className="font-heading text-2xl font-semibold">
                {org.name}
              </h1>
              {org.description && (
                <p className="mt-1 text-muted-foreground">{org.description}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={handleTabChange}
        className="space-y-6"
      >
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <Building className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="invitations" className="gap-2">
            <Mail className="h-4 w-4" />
            Invitations
          </TabsTrigger>
          {isAdmin && (
            <TabsTrigger value="settings" className="gap-2">
              <Settings className="h-4 w-4" />
              Settings
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab
            org={org}
            isAdmin={isAdmin}
            onUpdate={fetchData}
            orgId={orgId}
            members={members}
            currentUserId={user?.id}
          />
        </TabsContent>

        <TabsContent value="invitations">
          <InvitationsTab
            invitations={invitations}
            isAdmin={isAdmin}
            canInvite={org.can_invite ?? false}
            orgId={orgId}
            onUpdate={fetchData}
          />
        </TabsContent>

        {isAdmin && (
          <TabsContent value="settings">
            <SettingsTab orgId={orgId} />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}

// ─── Overview Tab ───────────────────────────────────────────────────

function OverviewTab({
  org,
  isAdmin,
  onUpdate,
  orgId,
  members,
  currentUserId,
}: {
  org: Organization;
  isAdmin: boolean;
  onUpdate: () => Promise<void>;
  orgId: string;
  members: OrganizationMembership[];
  currentUserId?: string;
}) {
  const router = useRouter();
  const { refreshUser } = useAuth();

  // Edit org state
  const [editing, setEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    name: org.name,
    description: org.description || "",
  });

  // Members state
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [isLeaving, setIsLeaving] = useState(false);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setIsSaving(true);
    try {
      await updateOrganization(orgId, form);
      toast.success("Organization updated");
      setEditing(false);
      await onUpdate();
    } catch (error) {
      if (error instanceof AxiosError) {
        toast.error(
          error.response?.data?.name?.[0] || "Failed to update organization",
        );
      }
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRemove(membershipId: string) {
    setRemovingId(membershipId);
    try {
      await removeMember(orgId, membershipId);
      toast.success("Member removed");
      await onUpdate();
    } catch (error) {
      if (error instanceof AxiosError) {
        toast.error(error.response?.data?.error || "Failed to remove member");
      }
    } finally {
      setRemovingId(null);
    }
  }

  async function handleLeave() {
    setIsLeaving(true);
    try {
      await leaveOrganization(orgId);
      await refreshUser();
      toast.success(`Left ${org.name}`);
      router.push("/organizations");
    } catch (error) {
      if (error instanceof AxiosError) {
        toast.error(
          error.response?.data?.error || "Failed to leave organization",
        );
      }
    } finally {
      setIsLeaving(false);
    }
  }

  const createdDate = org.created_at
    ? new Date(org.created_at).toLocaleDateString("en-US", {
        month: "short",
        year: "numeric",
      })
    : null;

  return (
    <div className="space-y-6">
      {/* Org Details Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Organization</CardTitle>
            {isAdmin && !editing && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditing(true)}
              >
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {editing ? (
            <form onSubmit={handleSave} className="space-y-4">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input
                  value={form.name}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, name: e.target.value }))
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  value={form.description}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      description: e.target.value,
                    }))
                  }
                  rows={3}
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={isSaving}>
                  {isSaving && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Save
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setEditing(false);
                    setForm({
                      name: org.name,
                      description: org.description || "",
                    });
                  }}
                >
                  Cancel
                </Button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div>
                <p className="text-lg font-semibold">{org.name}</p>
                {org.description && (
                  <p className="mt-1 text-sm text-muted-foreground">
                    {org.description}
                  </p>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-full border bg-muted/50 px-3 py-1 text-sm font-medium">
                  <Users className="h-3.5 w-3.5 text-muted-foreground" />
                  {org.member_count ?? members.length}{" "}
                  {(org.member_count ?? members.length) === 1
                    ? "member"
                    : "members"}
                </span>
                {createdDate && (
                  <span className="inline-flex items-center gap-1.5 rounded-full border bg-muted/50 px-3 py-1 text-sm font-medium">
                    <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                    Created {createdDate}
                  </span>
                )}
              </div>
              {org.address && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">
                    Address
                  </p>
                  <p className="text-sm">
                    {org.address.line1}
                    {org.address.line2 && `, ${org.address.line2}`}
                    <br />
                    {org.address.city}, {org.address.province_state}{" "}
                    {org.address.postal_code}
                    <br />
                    {org.address.country}
                  </p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Members Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Members</CardTitle>
              <CardDescription>
                {members.length} member{members.length !== 1 ? "s" : ""} in this
                organization
              </CardDescription>
            </div>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-destructive"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Leave
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Leave organization?</AlertDialogTitle>
                  <AlertDialogDescription>
                    You will lose access to {org.name}. You&apos;ll need a new
                    invitation to rejoin.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleLeave}
                    disabled={isLeaving}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    {isLeaving && (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    )}
                    Leave
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Joined</TableHead>
                {isAdmin && <TableHead className="w-12" />}
              </TableRow>
            </TableHeader>
            <TableBody>
              {members.map((membership) => (
                <TableRow key={membership.id}>
                  <TableCell className="font-medium">
                    {membership.user?.first_name} {membership.user?.last_name}
                    {membership.user?.id === currentUserId && (
                      <span className="ml-2 text-xs text-muted-foreground">
                        (you)
                      </span>
                    )}
                  </TableCell>
                  <TableCell>{membership.user?.email}</TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        membership.role === "ORG_ADMIN"
                          ? "default"
                          : "secondary"
                      }
                    >
                      {membership.role === "ORG_ADMIN" ? "Admin" : "Member"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {membership.created_at
                      ? new Date(membership.created_at).toLocaleDateString()
                      : "—"}
                  </TableCell>
                  {isAdmin && (
                    <TableCell>
                      {membership.user?.id !== currentUserId && (
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>
                                Remove member?
                              </AlertDialogTitle>
                              <AlertDialogDescription>
                                Remove {membership.user?.first_name}{" "}
                                {membership.user?.last_name} from the
                                organization?
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleRemove(membership.id!)}
                                disabled={removingId === membership.id}
                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                              >
                                {removingId === membership.id && (
                                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                )}
                                Remove
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      )}
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Settings Tab ───────────────────────────────────────────────────

function SettingsTab({ orgId }: { orgId: string }) {
  const [orgCategories, setOrgCategories] = useState<OrgRefItem[]>([]);
  const [orgLevels, setOrgLevels] = useState<OrgRefItem[]>([]);
  const [newCategoryTitle, setNewCategoryTitle] = useState("");
  const [newLevelTitle, setNewLevelTitle] = useState("");
  const [isAddingCategory, setIsAddingCategory] = useState(false);
  const [isAddingLevel, setIsAddingLevel] = useState(false);
  const [deletingCategoryId, setDeletingCategoryId] = useState<string | null>(
    null,
  );
  const [deletingLevelId, setDeletingLevelId] = useState<string | null>(null);

  useEffect(() => {
    listOrgJobCategories(orgId)
      .then((data) => setOrgCategories(data ?? []))
      .catch(() => toast.error("Failed to load job categories"));
    listOrgExperienceLevels(orgId)
      .then((data) => setOrgLevels(data ?? []))
      .catch(() => toast.error("Failed to load experience levels"));
  }, [orgId]);

  async function handleAddCategory(e: React.FormEvent) {
    e.preventDefault();
    const title = newCategoryTitle.trim();
    if (!title) return;
    setIsAddingCategory(true);
    try {
      const created = await createOrgJobCategory(orgId, title);
      setOrgCategories((prev) =>
        [...prev, created].sort((a, b) => a.title.localeCompare(b.title)),
      );
      setNewCategoryTitle("");
      toast.success(`Category "${created.title}" added`);
    } catch (error) {
      if (error instanceof AxiosError) {
        const msg =
          error.response?.data?.title?.[0] || "Failed to add category";
        toast.error(msg);
      } else {
        toast.error("Failed to add category");
      }
    } finally {
      setIsAddingCategory(false);
    }
  }

  async function handleDeleteCategory(categoryId: string, title: string) {
    setDeletingCategoryId(categoryId);
    try {
      await deleteOrgJobCategory(orgId, categoryId);
      setOrgCategories((prev) => prev.filter((c) => c.id !== categoryId));
      toast.success(`Category "${title}" deleted`);
    } catch (error) {
      if (error instanceof AxiosError) {
        const msg = error.response?.data?.detail || "Failed to delete category";
        toast.error(msg);
      } else {
        toast.error("Failed to delete category");
      }
    } finally {
      setDeletingCategoryId(null);
    }
  }

  async function handleAddLevel(e: React.FormEvent) {
    e.preventDefault();
    const title = newLevelTitle.trim();
    if (!title) return;
    setIsAddingLevel(true);
    try {
      const created = await createOrgExperienceLevel(orgId, title);
      setOrgLevels((prev) =>
        [...prev, created].sort((a, b) => a.title.localeCompare(b.title)),
      );
      setNewLevelTitle("");
      toast.success(`Experience level "${created.title}" added`);
    } catch (error) {
      if (error instanceof AxiosError) {
        const msg =
          error.response?.data?.title?.[0] || "Failed to add experience level";
        toast.error(msg);
      } else {
        toast.error("Failed to add experience level");
      }
    } finally {
      setIsAddingLevel(false);
    }
  }

  async function handleDeleteLevel(levelId: string, title: string) {
    setDeletingLevelId(levelId);
    try {
      await deleteOrgExperienceLevel(orgId, levelId);
      setOrgLevels((prev) => prev.filter((l) => l.id !== levelId));
      toast.success(`Experience level "${title}" deleted`);
    } catch (error) {
      if (error instanceof AxiosError) {
        const msg =
          error.response?.data?.detail || "Failed to delete experience level";
        toast.error(msg);
      } else {
        toast.error("Failed to delete experience level");
      }
    } finally {
      setDeletingLevelId(null);
    }
  }

  return (
    <div className="space-y-6">
      {/* Custom Job Categories */}
      <Card>
        <CardHeader>
          <CardTitle>Custom Job Categories</CardTitle>
          <CardDescription>
            Add custom job categories specific to your organization. Global
            categories are also available and cannot be deleted here.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleAddCategory} className="flex gap-2">
            <Input
              placeholder="New category title…"
              value={newCategoryTitle}
              onChange={(e) => setNewCategoryTitle(e.target.value)}
              className="flex-1"
            />
            <Button
              type="submit"
              disabled={isAddingCategory || !newCategoryTitle.trim()}
              size="sm"
            >
              {isAddingCategory ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              <span className="ml-1">Add</span>
            </Button>
          </form>
          <div className="divide-y rounded-md border">
            {orgCategories.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">
                No categories yet.
              </p>
            ) : (
              orgCategories.map((cat) => (
                <div
                  key={cat.id}
                  className="flex items-center justify-between px-3 py-2"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{cat.title}</span>
                    {cat.is_custom && (
                      <Badge variant="secondary" className="text-xs">
                        Custom
                      </Badge>
                    )}
                  </div>
                  {cat.is_custom && (
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive hover:text-destructive"
                          disabled={deletingCategoryId === cat.id}
                        >
                          {deletingCategoryId === cat.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="h-3.5 w-3.5" />
                          )}
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete category?</AlertDialogTitle>
                          <AlertDialogDescription>
                            Delete &quot;{cat.title}&quot;? This cannot be
                            undone. Categories in use by job profiles cannot be
                            deleted.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            onClick={() =>
                              handleDeleteCategory(cat.id, cat.title)
                            }
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Custom Experience Levels */}
      <Card>
        <CardHeader>
          <CardTitle>Custom Experience Levels</CardTitle>
          <CardDescription>
            Add custom experience levels specific to your organization. Global
            levels are also available and cannot be deleted here.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleAddLevel} className="flex gap-2">
            <Input
              placeholder="New experience level title…"
              value={newLevelTitle}
              onChange={(e) => setNewLevelTitle(e.target.value)}
              className="flex-1"
            />
            <Button
              type="submit"
              disabled={isAddingLevel || !newLevelTitle.trim()}
              size="sm"
            >
              {isAddingLevel ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              <span className="ml-1">Add</span>
            </Button>
          </form>
          <div className="divide-y rounded-md border">
            {orgLevels.length === 0 ? (
              <p className="py-4 text-center text-sm text-muted-foreground">
                No experience levels yet.
              </p>
            ) : (
              orgLevels.map((level) => (
                <div
                  key={level.id}
                  className="flex items-center justify-between px-3 py-2"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{level.title}</span>
                    {level.is_custom && (
                      <Badge variant="secondary" className="text-xs">
                        Custom
                      </Badge>
                    )}
                  </div>
                  {level.is_custom && (
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive hover:text-destructive"
                          disabled={deletingLevelId === level.id}
                        >
                          {deletingLevelId === level.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="h-3.5 w-3.5" />
                          )}
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>
                            Delete experience level?
                          </AlertDialogTitle>
                          <AlertDialogDescription>
                            Delete &quot;{level.title}&quot;? This cannot be
                            undone. Levels in use by job profiles cannot be
                            deleted.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            onClick={() =>
                              handleDeleteLevel(level.id, level.title)
                            }
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Invitations Tab ────────────────────────────────────────────────

function InvitationsTab({
  invitations,
  isAdmin,
  canInvite,
  orgId,
  onUpdate,
}: {
  invitations: OrganizationInvitation[];
  isAdmin: boolean;
  canInvite: boolean;
  orgId: string;
  onUpdate: () => Promise<void>;
}) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<MemberRole>("MEMBER");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  async function handleCancel(invitationId: string | undefined) {
    if (!invitationId) return;
    setActionLoading(`cancel-${invitationId}`);
    try {
      await cancelInvitation(orgId, invitationId);
      toast.success("Invitation cancelled");
      onUpdate();
    } catch (error) {
      if (error instanceof AxiosError) {
        toast.error(
          error.response?.data?.error || "Failed to cancel invitation",
        );
      }
    } finally {
      setActionLoading(null);
    }
  }

  async function handleResend(invitationId: string | undefined) {
    if (!invitationId) return;
    setActionLoading(`resend-${invitationId}`);
    try {
      const result = await resendInvitation(orgId, invitationId);
      if ((result as { email_sent?: boolean })?.email_sent) {
        toast.success("Invitation resent");
      } else {
        toast.success("Invitation refreshed (email delivery pending)");
      }
      onUpdate();
    } catch (error) {
      if (error instanceof AxiosError) {
        toast.error(
          error.response?.data?.error || "Failed to resend invitation",
        );
      }
    } finally {
      setActionLoading(null);
    }
  }

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    setIsSending(true);
    try {
      const result = await createInvitation(orgId, {
        email: inviteEmail,
        role: inviteRole,
      });
      if ((result as { email_sent?: boolean })?.email_sent) {
        toast.success(`Invitation sent to ${inviteEmail}`);
      } else {
        toast.success("Invitation created (email delivery pending)");
      }
      setDialogOpen(false);
      setInviteEmail("");
      setInviteRole("MEMBER");
      setIsSending(false);
      onUpdate();
    } catch (error) {
      setIsSending(false);
      if (error instanceof AxiosError) {
        const msg =
          error.response?.data?.email?.[0] ||
          error.response?.data?.error ||
          "Failed to send invitation";
        toast.error(msg);
      }
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Invitations</CardTitle>
            <CardDescription>Manage organization invitations</CardDescription>
          </div>
          {isAdmin && canInvite && (
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Send className="mr-2 h-4 w-4" />
                  Invite
                </Button>
              </DialogTrigger>
              <DialogContent>
                <form onSubmit={handleInvite}>
                  <DialogHeader>
                    <DialogTitle>Invite member</DialogTitle>
                    <DialogDescription>
                      Send an invitation email to join this organization.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="invite-email">Email</Label>
                      <Input
                        id="invite-email"
                        type="email"
                        placeholder="user@example.com"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Role</Label>
                      <Select
                        value={inviteRole}
                        onValueChange={(v) => setInviteRole(v as MemberRole)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="MEMBER">Member</SelectItem>
                          <SelectItem value="ORG_ADMIN">Admin</SelectItem>
                        </SelectContent>
                      </Select>
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
                    <Button type="submit" disabled={isSending}>
                      {isSending && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      Send invitation
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {invitations.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Mail className="mb-4 h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              No invitations sent yet
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Invited by</TableHead>
                <TableHead>Sent</TableHead>
                {isAdmin && (
                  <TableHead className="text-right">Actions</TableHead>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {invitations.map((inv) => (
                <TableRow key={inv.id}>
                  <TableCell className="font-medium">{inv.email}</TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        inv.role === "ORG_ADMIN" ? "default" : "secondary"
                      }
                    >
                      {inv.role === "ORG_ADMIN" ? "Admin" : "Member"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {inv.accepted_at ? (
                      <span className="inline-flex items-center gap-1 text-green-700">
                        <Check className="h-4 w-4" />
                        Accepted
                      </span>
                    ) : inv.is_expired ? (
                      <span className="inline-flex items-center gap-1 text-destructive">
                        <X className="h-4 w-4" />
                        Expired
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-yellow-700">
                        <Clock className="h-4 w-4" />
                        Pending
                      </span>
                    )}
                  </TableCell>
                  <TableCell>{inv.invited_by_email}</TableCell>
                  <TableCell>
                    {inv.created_at
                      ? new Date(inv.created_at).toLocaleDateString()
                      : "—"}
                  </TableCell>
                  {isAdmin && (
                    <TableCell className="text-right">
                      {!inv.accepted_at && (
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            title="Resend invitation"
                            disabled={actionLoading !== null}
                            onClick={() => handleResend(inv.id)}
                          >
                            {actionLoading === `resend-${inv.id}` ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <RotateCw className="h-4 w-4" />
                            )}
                          </Button>
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-destructive hover:text-destructive"
                                title="Cancel invitation"
                                disabled={actionLoading !== null}
                              >
                                {actionLoading === `cancel-${inv.id}` ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Ban className="h-4 w-4" />
                                )}
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>
                                  Cancel invitation?
                                </AlertDialogTitle>
                                <AlertDialogDescription>
                                  This will cancel the invitation sent to{" "}
                                  <strong>{inv.email}</strong>. They will no
                                  longer be able to join using the invitation
                                  link.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Keep</AlertDialogCancel>
                                <AlertDialogAction
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                  onClick={() => handleCancel(inv.id)}
                                >
                                  Cancel invitation
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      )}
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
