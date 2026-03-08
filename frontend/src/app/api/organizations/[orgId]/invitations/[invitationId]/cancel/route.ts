import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsInvitationsCancelDelete } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * DELETE /api/organizations/:orgId/invitations/:invitationId/cancel
 *
 * Cancel a pending invitation.
 * Only organization admins can cancel invitations.
 */
export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string; invitationId: string }> },
) {
  try {
    const { orgId, invitationId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsInvitationsCancelDelete({
        ...opts,
        path: { org_id: orgId, invitation_id: invitationId },
      }),
    );
    return NextResponse.json(response.data ?? { success: true });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
