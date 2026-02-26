"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Building2, Briefcase, LogOut, User } from "lucide-react";

export function AppNavbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

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

  const jobProfilesHref = user?.default_organization
    ? `/organizations/${user.default_organization}/job-profiles`
    : "/dashboard";

  const jobProfilesActive =
    /^\/organizations\/[^/]+\/job-profiles/.test(pathname) ||
    pathname === "/dashboard";

  const navLinks = [
    {
      href: jobProfilesHref,
      label: "Job Profiles",
      icon: Briefcase,
      isActive: jobProfilesActive,
    },
    {
      href: "/organizations",
      label: "Organizations",
      icon: Building2,
      isActive: pathname.startsWith("/organizations") && !jobProfilesActive,
    },
  ];

  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between px-6">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="flex items-center">
            <Image
              src="/icon.png"
              alt="Talentika"
              width={32}
              height={32}
              priority
            />
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            {navLinks.map((link) => (
              <Link key={link.label} href={link.href}>
                <Button
                  variant={link.isActive ? "secondary" : "ghost"}
                  size="sm"
                  className="gap-2"
                >
                  <link.icon className="h-4 w-4" />
                  {link.label}
                </Button>
              </Link>
            ))}
          </nav>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-9 w-9 rounded-full">
              <Avatar className="h-9 w-9">
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
    </header>
  );
}
