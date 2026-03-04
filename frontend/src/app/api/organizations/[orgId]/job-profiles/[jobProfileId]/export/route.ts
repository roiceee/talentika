import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsJobProfilesExportCreate } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/organizations/:orgId/job-profiles/:jobProfileId/export
 *
 * Request an async export of job applications.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string; jobProfileId: string }> },
) {
  try {
    const { orgId, jobProfileId } = await params;
    const body = await request.json();
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsJobProfilesExportCreate({
        ...opts,
        path: { org_id: orgId, job_profile_id: jobProfileId },
        body,
      }),
    );
    return NextResponse.json(response.data, { status: 201 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
