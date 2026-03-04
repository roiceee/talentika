import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsAnalyticsList } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/organizations/:orgId/analytics
 *
 * Proxy org-wide analytics data from the Django backend.
 */
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  try {
    const { orgId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsAnalyticsList({ ...opts, path: { org_id: orgId } }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
