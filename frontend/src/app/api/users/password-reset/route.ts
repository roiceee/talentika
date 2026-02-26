import { NextRequest, NextResponse } from "next/server";
import { apiUsersPasswordResetCreate } from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/users/password-reset
 *
 * Request a password reset email. Public endpoint — no auth required.
 * Forwards to Django via the SDK.
 *
 * Request body: { email: string }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await apiUsersPasswordResetCreate({
      client,
      body: { email: body.email },
    });

    return NextResponse.json(response.data, { status: 200 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
