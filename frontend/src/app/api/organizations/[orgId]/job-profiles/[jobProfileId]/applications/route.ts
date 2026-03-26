import { NextRequest, NextResponse } from "next/server";
import { getAccessToken } from "@/lib/server/tokens";
import { errorResponse } from "@/lib/server/errors";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/**
 * GET /api/organizations/:orgId/job-profiles/:jobProfileId/applications
 *
 * List job applications with server-side pagination, search, filter, ordering.
 * Forwards query params: page, page_size, search, status, ordering
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string; jobProfileId: string }> },
) {
  try {
    const { orgId, jobProfileId } = await params;
    const token = await getAccessToken();

    // Forward allowed query params to the backend
    const incoming = request.nextUrl.searchParams;
    const qs = new URLSearchParams();
    for (const key of ["page", "page_size", "search", "status", "ordering"]) {
      const val = incoming.get(key);
      if (val !== null && val !== "") qs.set(key, val);
    }
    // Multi-value params
    for (const key of ["skill", "trait"]) {
      for (const val of incoming.getAll(key)) {
        if (val !== "") qs.append(key, val);
      }
    }
    const queryString = qs.toString();
    const url = `${BACKEND_URL}/api/organizations/${orgId}/job-profiles/${jobProfileId}/applications/${queryString ? `?${queryString}` : ""}`;

    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
