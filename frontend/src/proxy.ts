import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js Edge Middleware
 *
 * Handles:
 * 1. CSRF validation for state-changing API requests (POST, PUT, PATCH, DELETE)
 *    - Note: Individual route handlers also validate CSRF for defense-in-depth.
 *      This middleware provides an early rejection at the edge.
 * 2. Ensuring CSRF token cookie exists for all page requests.
 */
export function proxy(request: NextRequest) {
  const { pathname, method } = {
    pathname: request.nextUrl.pathname,
    method: request.method,
  };

  // Only apply to our BFF API routes
  if (pathname.startsWith("/api/")) {
    // CSRF validation for state-changing methods
    if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
      // Skip CSRF check for the CSRF token endpoint itself
      if (pathname === "/api/auth/csrf") {
        return NextResponse.next();
      }

      // Skip CSRF check for the refresh endpoint (called programmatically)
      if (pathname === "/api/auth/refresh") {
        return NextResponse.next();
      }

      // Skip CSRF check for public invitation endpoints — these are accessed by
      // unauthenticated users who don't have a CSRF cookie yet.
      if (pathname === "/api/invitations/validate") {
        return NextResponse.next();
      }

      const csrfCookie = request.cookies.get("csrf_token")?.value;
      const csrfHeader = request.headers.get("x-csrf-token");

      if (!csrfCookie || !csrfHeader || csrfCookie !== csrfHeader) {
        return NextResponse.json(
          { error: "CSRF validation failed" },
          { status: 403 },
        );
      }
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/api/:path*"],
};
