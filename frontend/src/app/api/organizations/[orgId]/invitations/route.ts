import { NextRequest, NextResponse } from "next/server";
import {
  apiOrganizationsInvitationsListList,
  apiOrganizationsInvitationsCreate,
} from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/organizations/:orgId/invitations
 *
 * List all invitations for the organization.
 */
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  try {
    const { orgId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsInvitationsListList({
        ...opts,
        path: { org_id: orgId },
      }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}

/**
 * POST /api/organizations/:orgId/invitations
 *
 * Create an invitation to join the organization.
 * Only org admins of APPROVED organizations can send invitations.
 *
 * Request body: { email: string, role: string }
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  try {
    const { orgId } = await params;
    const body = await request.json();
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsInvitationsCreate({
        ...opts,
        path: { org_id: orgId },
        body,
      }),
    );
    return NextResponse.json(response.data, { status: 201 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
