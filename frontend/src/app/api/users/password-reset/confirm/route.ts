import { NextRequest, NextResponse } from "next/server";
import { apiUsersPasswordResetConfirmCreate } from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/users/password-reset/confirm
 *
 * Confirm a password reset using the token from the email link.
 * Public endpoint — no auth required.
 * Forwards to Django via the SDK.
 *
 * Request body: { token: string, new_password: string, new_password_confirm: string }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await apiUsersPasswordResetConfirmCreate({
      client,
      body: {
        token: body.token,
        new_password: body.new_password,
        new_password_confirm: body.new_password_confirm,
      },
    });

    return NextResponse.json(response.data, { status: 200 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
