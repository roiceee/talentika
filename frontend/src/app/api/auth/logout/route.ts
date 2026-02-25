import { NextResponse } from "next/server";
import { clearTokens } from "@/lib/server/tokens";

/**
 * POST /api/auth/logout
 *
 * Clears all auth tokens from httpOnly cookies.
 */
export async function POST() {
  await clearTokens();
  return NextResponse.json({ success: true });
}
