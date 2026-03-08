import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsInvitationsResendCreate } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/organizations/:orgId/invitations/:invitationId/resend
 *
 * Resend an invitation email with a fresh token and expiration.
 * Only organization admins can resend invitations.
 */
export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string; invitationId: string }> },
) {
  try {
    const { orgId, invitationId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsInvitationsResendCreate({
        ...opts,
        path: { org_id: orgId, invitation_id: invitationId },
      }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
