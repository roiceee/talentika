import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsLeaveDelete } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * DELETE /api/organizations/:orgId/leave
 *
 * Leave the organization. Any member can leave.
 * Admins can only leave if there is at least one other admin.
 */
export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  try {
    const { orgId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsLeaveDelete({ ...opts, path: { org_id: orgId } }),
    );
    return NextResponse.json(response.data ?? { success: true });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
