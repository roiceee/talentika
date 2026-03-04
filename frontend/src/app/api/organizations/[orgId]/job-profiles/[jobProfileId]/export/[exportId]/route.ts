import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsJobProfilesExportRead } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/organizations/:orgId/job-profiles/:jobProfileId/export/:exportId
 *
 * Poll the status of an export job.
 */
export async function GET(
  _request: NextRequest,
  {
    params,
  }: {
    params: Promise<{
      orgId: string;
      jobProfileId: string;
      exportId: string;
    }>;
  },
) {
  try {
    const { orgId, jobProfileId, exportId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsJobProfilesExportRead({
        ...opts,
        path: {
          org_id: orgId,
          job_profile_id: jobProfileId,
          export_id: exportId,
        },
      }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
