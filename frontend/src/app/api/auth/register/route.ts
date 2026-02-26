import { NextRequest, NextResponse } from "next/server";
import {
  apiUsersAuthRegisterCreate,
  apiUsersAuthLoginCreate,
} from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { setTokens } from "@/lib/server/tokens";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/auth/register
 *
 * BFF register endpoint. Proxies registration data to Django,
 * then automatically logs in the user and stores tokens in httpOnly cookies.
 *
 * Request body: UserWritable (email, username, first_name, last_name, password, password_confirm, invitation_token?)
 * Response: { success: true, user: User } on success, or Django error details.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Register the user — any validation error from Django is thrown here
    const registerResponse = await apiUsersAuthRegisterCreate({
      client,
      body,
    });

    // Auto-login after successful registration
    const loginResponse = await apiUsersAuthLoginCreate({
      client,
      body: { email: body.email, password: body.password },
    });

    if (loginResponse.data?.access && loginResponse.data?.refresh) {
      await setTokens(loginResponse.data.access, loginResponse.data.refresh);
    }

    return NextResponse.json(
      { success: true, user: registerResponse.data },
      { status: 201 },
    );
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
