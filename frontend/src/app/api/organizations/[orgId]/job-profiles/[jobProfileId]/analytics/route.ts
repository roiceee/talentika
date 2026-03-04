import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsJobProfilesAnalyticsList } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

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
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsJobProfilesAnalyticsList({
        ...opts,
        path: { org_id: orgId, job_profile_id: jobProfileId },
      }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
