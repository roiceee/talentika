import { NextRequest, NextResponse } from "next/server";
import { apiUsersPasswordResetCreate } from "@/lib/client";
import { client } from "@/lib/client/client.gen";

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
    if (isAxiosError(error)) {
      return NextResponse.json(error.response.data, {
        status: error.response.status,
      });
    }
    return NextResponse.json(
      { error: "An unexpected error occurred" },
      { status: 500 },
    );
  }
}

function isAxiosError(
  error: unknown,
): error is { response: { status: number; data: unknown } } {
  return (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof (error as { response: unknown }).response === "object"
  );
}
