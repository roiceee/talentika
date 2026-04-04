import { NextRequest, NextResponse } from "next/server";
import { apiJobProfilesDeleteDelete } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * DELETE /api/organizations/:orgId/job-profiles/:jobProfileId
 *
 * Soft-delete a job profile. Only organization admins can do this.
 */
export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ jobProfileId: string }> },
) {
  try {
    const { jobProfileId } = await params;
    await authenticatedSdkCall((opts) =>
      apiJobProfilesDeleteDelete({ ...opts, path: { job_id: jobProfileId } }),
    );
    return new NextResponse(null, { status: 204 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
