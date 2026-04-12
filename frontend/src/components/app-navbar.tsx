"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { toast } from "sonner";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Building2,
  Briefcase,
  BarChart3,
  LogOut,
  User,
  ChevronsUpDown,
  Check,
  Settings,
} from "lucide-react";
import { listOrganizations, setDefaultOrganization } from "@/lib/api";
import type { OrganizationListItem } from "@/types";

export function AppNavbar() {
  const { user, logout, refreshUser } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const [orgs, setOrgs] = useState<OrganizationListItem[]>([]);
  const [orgDropdownOpen, setOrgDropdownOpen] = useState(false);
  const [switchingOrgId, setSwitchingOrgId] = useState<string | null>(null);

  // Reload orgs on every route change so newly created orgs appear immediately
  useEffect(() => {
    listOrganizations()
      .then(setOrgs)
      .catch(() => {});
  }, [pathname]);

  const currentOrg = orgs.find((o) => o.id === user?.default_organization);

  const initials = user
    ? `${user.first_name?.[0] || ""}${user.last_name?.[0] || ""}`.toUpperCase() ||
      user.email?.[0]?.toUpperCase() ||
      "?"
    : "?";

  async function handleLogout() {
    try {
      await logout();
      toast.success("Logged out");
      router.push("/login");
    } catch {
      toast.error("Failed to log out");
    }
  }

  async function handleSwitchOrg(orgId: string) {
    if (orgId === user?.default_organization) return;
    setSwitchingOrgId(orgId);
    try {
      await setDefaultOrganization(orgId);
      await refreshUser();
      setOrgDropdownOpen(false);
      // Reload job profiles for the new org
      router.push("/job-profiles");
      router.refresh();
      toast.success("Switched organization");
    } catch {
      toast.error("Failed to switch organization");
    } finally {
      setSwitchingOrgId(null);
    }
  }

  const jobProfilesActive = pathname.startsWith("/job-profiles");
  const analyticsActive = pathname.startsWith("/analytics");

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-border shadow-sm">
      <div className="mx-auto w-full max-w-[1600px] flex h-14 items-center justify-between px-6">
        <div className="flex items-center gap-5">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <Image
              src="/icon.png"
              alt="Talentika"
              width={30}
              height={30}
              priority
            />
            <span className="font-heading text-base text-foreground hidden sm:block">
              Talentika
            </span>
          </Link>

          <div className="h-5 w-px bg-border hidden md:block" />

          {/* Main nav links */}
          <nav className="hidden items-center gap-0.5 md:flex">
            <Link href="/job-profiles">
              <Button
                variant="ghost"
                size="sm"
                className={`gap-2 relative ${
                  jobProfilesActive
                    ? "text-primary font-semibold bg-primary/8 hover:bg-primary/12"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Briefcase className="h-4 w-4" />
                Job Profiles
                {jobProfilesActive && (
                  <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-primary rounded-full" />
                )}
              </Button>
            </Link>
            <Link href="/analytics">
              <Button
                variant="ghost"
                size="sm"
                className={`gap-2 relative ${
                  analyticsActive
                    ? "text-primary font-semibold bg-primary/8 hover:bg-primary/12"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <BarChart3 className="h-4 w-4" />
                Analytics
                {analyticsActive && (
                  <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-primary rounded-full" />
                )}
              </Button>
            </Link>
          </nav>
        </div>

        {/* Right side: org switcher + user dropdown */}
        <div className="flex items-center gap-2">
          {/* Org settings shortcut */}
          {currentOrg?.id && (
            <Link href={`/organizations/${currentOrg.id}?tab=settings`}>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 text-muted-foreground hover:text-foreground"
                title="Org Settings"
              >
                <Settings className="h-4 w-4" />
              </Button>
            </Link>
          )}

          {/* Organization switcher */}
          <DropdownMenu
            open={orgDropdownOpen}
            onOpenChange={(open) => {
              setOrgDropdownOpen(open);
              if (open) {
                listOrganizations()
                  .then(setOrgs)
                  .catch(() => {});
              }
            }}
          >
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="gap-2 max-w-52 h-9 border-border/80 hover:border-primary/40 hover:bg-primary/5 transition-colors"
              >
                <Avatar className="h-5 w-5 shrink-0">
                  {currentOrg?.profile_picture_url && (
                    <AvatarImage
                      src={currentOrg.profile_picture_url}
                      alt={currentOrg.name}
                    />
                  )}
                  <AvatarFallback className="bg-primary text-primary-foreground text-[10px]">
                    {currentOrg?.name?.[0]?.toUpperCase() ?? (
                      <Building2 className="h-3 w-3" />
                    )}
                  </AvatarFallback>
                </Avatar>
                <span className="truncate">
                  {currentOrg?.name ?? "Select org"}
                </span>
                <ChevronsUpDown className="ml-auto h-3.5 w-3.5 shrink-0 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-60">
              <DropdownMenuLabel className="text-xs text-muted-foreground font-normal">
                Your organizations
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              {orgs.length === 0 && (
                <DropdownMenuItem disabled>No organizations</DropdownMenuItem>
              )}
              {[...orgs]
                .sort((a, b) =>
                  a.id === user?.default_organization
                    ? -1
                    : b.id === user?.default_organization
                      ? 1
                      : 0,
                )
                .map((org) => {
                  const isActive = org.id === user?.default_organization;
                  const isSwitching = switchingOrgId === org.id;
                  return (
                    <DropdownMenuItem
                      key={org.id}
                      onClick={() => handleSwitchOrg(org.id!)}
                      disabled={isSwitching}
                      className="gap-2"
                    >
                      <Avatar className="h-5 w-5 shrink-0">
                        {org.profile_picture_url && (
                          <AvatarImage
                            src={org.profile_picture_url}
                            alt={org.name}
                          />
                        )}
                        <AvatarFallback className="bg-muted text-muted-foreground text-[10px]">
                          {org.name?.[0]?.toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <span className="truncate flex-1">{org.name}</span>
                      {isActive && (
                        <Check className="h-3.5 w-3.5 shrink-0 text-primary" />
                      )}
                    </DropdownMenuItem>
                  );
                })}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => {
                  setOrgDropdownOpen(false);
                  router.push("/organizations");
                }}
                className="gap-2"
              >
                <Settings className="h-4 w-4" />
                Manage organizations
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* User dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-9 w-9 rounded-full">
                <Avatar className="h-9 w-9">
                  {user?.profile_picture_url && (
                    <AvatarImage src={user.profile_picture_url} alt="Profile" />
                  )}
                  <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                    {initials}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="flex items-center gap-2 p-2">
                <div className="flex flex-col space-y-0.5">
                  <p className="text-sm font-medium">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="text-xs text-muted-foreground">{user?.email}</p>
                </div>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/profile")}>
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
