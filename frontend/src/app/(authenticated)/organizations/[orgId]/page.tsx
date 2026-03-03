"use client";

import { useEffect, useState, useCallback, use } from "react";
import { useRouter } from "next/navigation";
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
import {
  ArrowLeft,
  Building2,
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
} from "lucide-react";
import Link from "next/link";

export default function OrganizationDetailPage({
  params,
}: {
  params: Promise<{ orgId: string }>;
}) {
  const { orgId } = use(params);
  const router = useRouter();
  const { user } = useAuth();
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
          <div>
            <h1 className="font-heading text-2xl font-semibold">{org.name}</h1>
            {org.description && (
              <p className="mt-1 text-muted-foreground">{org.description}</p>
            )}
          </div>
          <Badge
            variant="outline"
            className={
              org.status === "APPROVED"
                ? "bg-green-100 text-green-800"
                : "bg-yellow-100 text-yellow-800"
            }
          >
            {org.status}
          </Badge>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <Building2 className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="members" className="gap-2">
            <Users className="h-4 w-4" />
            Members ({members.length})
          </TabsTrigger>
          <TabsTrigger value="invitations" className="gap-2">
            <Mail className="h-4 w-4" />
            Invitations
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab
            org={org}
            isAdmin={isAdmin}
            onUpdate={fetchData}
            orgId={orgId}
          />
        </TabsContent>

        <TabsContent value="members">
          <MembersTab
            members={members}
            isAdmin={isAdmin}
            currentUserId={user?.id}
            orgId={orgId}
            orgName={org.name}
            onUpdate={fetchData}
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
}: {
  org: Organization;
  isAdmin: boolean;
  onUpdate: () => Promise<void>;
  orgId: string;
}) {
  const [editing, setEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    name: org.name,
    description: org.description || "",
  });

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

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Organization details</CardTitle>
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
                {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
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
              <p className="text-sm font-medium text-muted-foreground">Name</p>
              <p>{org.name}</p>
            </div>
            {org.description && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Description
                </p>
                <p>{org.description}</p>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Status
                </p>
                <p>{org.status}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Members
                </p>
                <p>{org.member_count}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Created
                </p>
                <p>
                  {org.created_at
                    ? new Date(org.created_at).toLocaleDateString()
                    : "—"}
                </p>
              </div>
              {org.approved_at && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Approved
                  </p>
                  <p>{new Date(org.approved_at).toLocaleDateString()}</p>
                </div>
              )}
            </div>
            {org.address && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Address
                </p>
                <p>
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
  );
}

// ─── Members Tab ────────────────────────────────────────────────────

function MembersTab({
  members,
  isAdmin,
  currentUserId,
  orgId,
  orgName,
  onUpdate,
}: {
  members: OrganizationMembership[];
  isAdmin: boolean;
  currentUserId?: string;
  orgId: string;
  orgName: string;
  onUpdate: () => Promise<void>;
}) {
  const router = useRouter();
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [isLeaving, setIsLeaving] = useState(false);

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
      toast.success(`Left ${orgName}`);
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

  return (
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
              <Button variant="outline" size="sm" className="text-destructive">
                <LogOut className="mr-2 h-4 w-4" />
                Leave
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Leave organization?</AlertDialogTitle>
                <AlertDialogDescription>
                  You will lose access to {orgName}. You&apos;ll need a new
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
                      membership.role === "ORG_ADMIN" ? "default" : "secondary"
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
                            <AlertDialogTitle>Remove member?</AlertDialogTitle>
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
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
