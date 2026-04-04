import { NextRequest, NextResponse } from "next/server";
import { getAccessToken } from "@/lib/server/tokens";
import { errorResponse } from "@/lib/server/errors";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/**
 * POST /api/organizations/:orgId/job-profiles/:jobProfileId/applications/bulk
 *
 * Bulk upload resumes for a job profile. Forwards multipart form data directly
 * to the Django backend. Returns per-file results.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string; jobProfileId: string }> },
) {
  try {
    const { orgId, jobProfileId } = await params;
    const token = await getAccessToken();
    const formData = await request.formData();

    const url = `${BACKEND_URL}/api/organizations/${orgId}/job-profiles/${jobProfileId}/applications/bulk/`;

    const res = await fetch(url, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data, { status: 201 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
