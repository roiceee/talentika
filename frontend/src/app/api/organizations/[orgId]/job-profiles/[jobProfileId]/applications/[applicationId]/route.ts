import { NextRequest, NextResponse } from "next/server";
import {
  apiOrganizationsJobProfilesApplicationsRead,
  apiOrganizationsJobProfilesApplicationsDeleteDelete,
} from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/organizations/:orgId/job-profiles/:jobProfileId/applications/:applicationId
 *
 * Get a specific job application detail.
 */
export async function GET(
  _request: NextRequest,
  {
    params,
  }: {
    params: Promise<{
      orgId: string;
      jobProfileId: string;
      applicationId: string;
    }>;
  },
) {
  try {
    const { orgId, jobProfileId, applicationId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsJobProfilesApplicationsRead({
        ...opts,
        path: {
          org_id: orgId,
          job_profile_id: jobProfileId,
          job_application_id: applicationId,
        },
      }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}

/**
 * DELETE /api/organizations/:orgId/job-profiles/:jobProfileId/applications/:applicationId
 *
 * Soft-delete a job application. Only organization admins can do this.
 */
export async function DELETE(
  _request: NextRequest,
  {
    params,
  }: {
    params: Promise<{
      orgId: string;
      jobProfileId: string;
      applicationId: string;
    }>;
  },
) {
  try {
    const { orgId, jobProfileId, applicationId } = await params;
    await authenticatedSdkCall((opts) =>
      apiOrganizationsJobProfilesApplicationsDeleteDelete({
        ...opts,
        path: {
          org_id: orgId,
          job_profile_id: jobProfileId,
          job_application_id: applicationId,
        },
      }),
    );
    return new NextResponse(null, { status: 204 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
