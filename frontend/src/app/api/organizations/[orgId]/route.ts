import { NextRequest, NextResponse } from "next/server";
import {
  apiOrganizationsRead,
  apiOrganizationsUpdatePartialUpdate,
} from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/organizations/:orgId
 *
 * Get detailed information about a specific organization.
 */
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  try {
    const { orgId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsRead({ ...opts, path: { org_id: orgId } }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}

/**
 * PATCH /api/organizations/:orgId
 *
 * Update organization details. Only organization admins can update.
 *
 * Request body: { name?: string, description?: string }
 */
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  try {
    const { orgId } = await params;
    const body = await request.json();
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsUpdatePartialUpdate({
        ...opts,
        path: { org_id: orgId },
        body,
      }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
