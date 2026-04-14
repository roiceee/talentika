import { NextRequest, NextResponse } from "next/server";
import { apiOrganizationsMembersDelete } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { getAccessToken } from "@/lib/server/tokens";
import { errorResponse } from "@/lib/server/errors";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/**
 * PATCH /api/organizations/:orgId/members/:membershipId
 *
 * Update a member's role. Only organization admins can do this.
 */
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string; membershipId: string }> },
) {
  try {
    const { orgId, membershipId } = await params;
    const token = await getAccessToken();
    const body = await request.json();

    const res = await fetch(
      `${BACKEND_URL}/api/organizations/${orgId}/members/${membershipId}/role/`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      },
    );

    const data = await res.json();
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}

/**
 * DELETE /api/organizations/:orgId/members/:membershipId
 *
 * Remove a member from the organization.
 * Only organization admins can remove members.
 */
export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string; membershipId: string }> },
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
