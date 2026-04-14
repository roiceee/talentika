import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsJobProfilesDeleteDelete } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * DELETE /api/organizations/:orgId/job-profiles/:jobProfileId
 *
 * Soft-delete a job profile. Only organization admins can do this.
 * Uses the org-scoped backend endpoint so membership is verified against
 * the correct organization.
 */
export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string; jobProfileId: string }> },
) {
  try {
    const { orgId, jobProfileId } = await params;
    await authenticatedSdkCall((opts) =>
      apiOrganizationsJobProfilesDeleteDelete({
        ...opts,
        path: { org_id: orgId, job_id: jobProfileId },
      }),
    );
    return new NextResponse(null, { status: 204 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
