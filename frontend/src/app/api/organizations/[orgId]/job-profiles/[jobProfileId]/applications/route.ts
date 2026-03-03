import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsJobProfilesApplicationsList } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/organizations/:orgId/job-profiles/:jobProfileId/applications
 *
 * List all job applications for a specific job profile in an organization.
 */
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string; jobProfileId: string }> },
) {
  try {
    const { orgId, jobProfileId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsJobProfilesApplicationsList({
        ...opts,
        path: { org_id: orgId, job_profile_id: jobProfileId },
      }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
