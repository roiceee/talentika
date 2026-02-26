import { NextRequest, NextResponse } from "next/server";
import { apiUsersAuthLoginCreate } from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { setTokens } from "@/lib/server/tokens";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/auth/login
 *
 * BFF login endpoint. Proxies credentials to Django, then stores
 * the returned JWT tokens in httpOnly cookies.
 *
 * Request body: { email: string, password: string }
 * Response: { success: true } on success, or Django error details.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json(
        { error: "Email and password are required" },
        { status: 400 },
      );
    }

    const response = await apiUsersAuthLoginCreate({
      client,
      body: { email, password },
    });

    const { access, refresh } = response.data ?? {};
    if (!access || !refresh) {
      return NextResponse.json(
        { error: "Invalid credentials" },
        { status: 401 },
      );
    }
    await setTokens(access, refresh);
    return NextResponse.json({ success: true });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
