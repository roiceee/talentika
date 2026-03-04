import { NextRequest, NextResponse } from "next/server";
import { getAccessToken } from "@/lib/server/tokens";
import { errorResponse } from "@/lib/server/errors";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/**
 * GET /api/organizations/:orgId/job-profiles/:jobProfileId/analytics
 *
 * Proxy analytics data from the Django backend.
 */
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string; jobProfileId: string }> },
) {
  try {
    const { orgId, jobProfileId } = await params;
    const token = await getAccessToken();

    const url = `${BACKEND_URL}/api/organizations/${orgId}/job-profiles/${jobProfileId}/analytics/`;

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
