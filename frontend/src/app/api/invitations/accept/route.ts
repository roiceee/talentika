import { NextRequest, NextResponse } from "next/server";
import { apiInvitationsAcceptCreate } from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/invitations/accept
 *
 * Accept an invitation to join an organization.
 * Requires authentication - user must be signed in.
 *
 * Request body: { token: string }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await authenticatedSdkCall((opts) =>
      apiInvitationsAcceptCreate({ ...opts, body }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
