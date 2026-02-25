import { NextResponse } from "next/server";
import { refreshAccessToken } from "@/lib/server/api-client";

/**
 * POST /api/auth/refresh
 *
 * Manually trigger a token refresh. Called when the client detects
 * an expired access token. The refresh token is read from httpOnly cookies.
 *
 * On success, new tokens are stored in cookies automatically.
 */
export async function POST() {
  const newAccessToken = await refreshAccessToken();

  if (newAccessToken) {
    return NextResponse.json({ success: true });
  }

  return NextResponse.json(
    { error: "Token refresh failed. Please log in again." },
    { status: 401 },
  );
}
