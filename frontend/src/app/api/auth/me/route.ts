import { NextResponse } from "next/server";
import { getAuthenticatedUser } from "@/lib/server/api-client";

/**
 * GET /api/auth/me
 *
 * Returns the current authenticated user's profile.
 * Uses the access token from httpOnly cookies and handles auto-refresh.
 */
export async function GET() {
  const user = await getAuthenticatedUser();

  if (user) {
    return NextResponse.json(user);
  }

  return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
}
