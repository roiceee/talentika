import { NextRequest, NextResponse } from "next/server";
import {
  apiJobProfilesRead,
  apiJobProfilesUpdatePartialUpdate,
} from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { client } from "@/lib/client/client.gen";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/job-profiles/:jobId
 *
 * Get detailed information about a specific job profile (public endpoint).
 */
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> },
) {
  try {
    const { jobId } = await params;
    // Public endpoint — no auth required
    const response = await apiJobProfilesRead({
      client,
      path: { job_id: jobId },
    });
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}

/**
 * PATCH /api/job-profiles/:jobId
 *
 * Update an existing job profile.
 * Only organization admins can update job profiles.
 */
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> },
) {
  try {
    const { jobId } = await params;
    const body = await request.json();
    const response = await authenticatedSdkCall((opts) =>
      apiJobProfilesUpdatePartialUpdate({
        ...opts,
        path: { job_id: jobId },
        body,
      }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
