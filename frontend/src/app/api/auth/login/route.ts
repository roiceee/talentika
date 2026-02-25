import { NextRequest, NextResponse } from "next/server";
import { apiUsersAuthLoginCreate } from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { setTokens } from "@/lib/server/tokens";

/**
 * POST /api/auth/login
 *
 * BFF login endpoint. Proxies credentials to Django, then stores
 * the returned JWT tokens in httpOnly cookies.
 *
 * Request body: { email: string, password: string }
 * Response: { success: true } on success, or error details.
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

    if (response.data?.access && response.data?.refresh) {
      await setTokens(response.data.access, response.data.refresh);
      return NextResponse.json({ success: true });
    }

    return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
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
