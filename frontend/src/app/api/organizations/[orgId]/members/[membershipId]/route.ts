import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsMembersDelete } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * DELETE /api/organizations/:orgId/members/:membershipId
 *
 * Remove a member from the organization.
 * Only organization admins can remove members.
 */
export async function DELETE(
  _request: NextRequest,
  {
    params,
  }: { params: Promise<{ orgId: string; membershipId: string }> },
) {
  try {
    const { orgId, membershipId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsMembersDelete({
        ...opts,
        path: { org_id: orgId, membership_id: membershipId },
      }),
    );
    return NextResponse.json(response.data ?? { success: true });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
