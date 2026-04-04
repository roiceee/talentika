import { NextRequest, NextResponse } from "next/server";
import {
  apiUsersProfileUpdatePartialUpdate,
  apiUsersProfileDeleteDelete,
} from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * PATCH /api/users/profile
 *
 * Update the current user's profile.
 *
 * Request body: { username?: string, first_name?: string, last_name?: string }
 */
export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await authenticatedSdkCall((opts) =>
      apiUsersProfileUpdatePartialUpdate({ ...opts, body }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}

/**
 * DELETE /api/users/profile
 *
 * Soft-delete the authenticated user's account.
 */
export async function DELETE() {
  try {
    await authenticatedSdkCall((opts) => apiUsersProfileDeleteDelete(opts));
    return new NextResponse(null, { status: 204 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
