import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsJobProfilesList } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/organizations/:orgId/job-profiles
 *
 * List all job profiles for a specific organization.
 */
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  try {
    const { orgId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsJobProfilesList({ ...opts, path: { org_id: orgId } }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
