import { NextRequest, NextResponse } from "next/server";
import {
  apiUsersAuthRegisterCreate,
  apiUsersAuthLoginCreate,
} from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { setTokens } from "@/lib/server/tokens";

/**
 * POST /api/auth/register
 *
 * BFF register endpoint. Proxies registration data to Django,
 * then automatically logs in the user and stores tokens in httpOnly cookies.
 *
 * Request body: UserWritable (email, username, first_name, last_name, password, password_confirm, invitation_token?)
 * Response: { success: true, user: User } on success, or error details.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Register the user via Django API
    const registerResponse = await apiUsersAuthRegisterCreate({
      client,
      body,
    });

    if (!registerResponse.data) {
      return NextResponse.json(
        { error: "Registration failed" },
        { status: 400 },
      );
    }

    // Auto-login after successful registration
    const loginResponse = await apiUsersAuthLoginCreate({
      client,
      body: { email: body.email, password: body.password },
    });

    if (loginResponse.data?.access && loginResponse.data?.refresh) {
      await setTokens(loginResponse.data.access, loginResponse.data.refresh);
      return NextResponse.json(
        { success: true, user: registerResponse.data },
        { status: 201 },
      );
    }

    // Registration succeeded but auto-login failed — still return success
    return NextResponse.json(
      { success: true, user: registerResponse.data, loginRequired: true },
      { status: 201 },
    );
  } catch (error: unknown) {
    if (
      error &&
      typeof error === "object" &&
      "response" in error &&
      error.response &&
      typeof error.response === "object" &&
      "status" in error.response &&
      "data" in error.response
    ) {
      const axiosError = error as {
        response: { status: number; data: unknown };
      };
      return NextResponse.json(axiosError.response.data, {
        status: axiosError.response.status,
      });
    }

    return NextResponse.json(
      { error: "An unexpected error occurred" },
      { status: 500 },
    );
  }
}
