import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { randomBytes } from "crypto";

/**
 * GET /api/auth/csrf
 *
 * Returns a CSRF token. The token is set as a non-httpOnly cookie
 * (so JavaScript can read it) and also returned in the response body.
 *
 * The browser must send this token back as the `X-CSRF-Token` header
 * on all state-changing requests (POST, PUT, PATCH, DELETE).
 *
 * The edge middleware validates that the header matches the cookie.
 */
export async function GET() {
  const cookieStore = await cookies();
  let csrfToken = cookieStore.get("csrf_token")?.value;

  if (!csrfToken) {
    csrfToken = randomBytes(32).toString("hex");
  }

  const response = NextResponse.json({ csrfToken });

  response.cookies.set("csrf_token", csrfToken, {
    httpOnly: false, // Must be readable by JavaScript
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24, // 24 hours
  });

  return response;
}
