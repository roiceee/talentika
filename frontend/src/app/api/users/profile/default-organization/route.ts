import { NextRequest, NextResponse } from "next/server";
import { apiUsersProfileDefaultOrganizationPartialUpdate } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * PATCH /api/users/profile/default-organization
 *
 * Set or clear the authenticated user's default organization.
 *
 * Request body: { default_organization: string | null }
 */
export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await authenticatedSdkCall((opts) =>
      apiUsersProfileDefaultOrganizationPartialUpdate({ ...opts, body }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
