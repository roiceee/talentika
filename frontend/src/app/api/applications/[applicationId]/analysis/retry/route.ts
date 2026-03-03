import { NextRequest, NextResponse } from "next/server";
import { getAccessToken } from "@/lib/server/tokens";
import { getAuthHeaders } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/**
 * POST /api/applications/:applicationId/analysis/retry
 *
 * Re-trigger a failed analysis pipeline.
 */
export async function POST(
  _request: NextRequest,
  {
    params,
  }: {
    params: Promise<{ applicationId: string }>;
  },
) {
  try {
    const { applicationId } = await params;
    const accessToken = await getAccessToken();
    if (!accessToken) {
      return NextResponse.json(
        { detail: "Not authenticated" },
        { status: 401 },
      );
    }
    const headers = getAuthHeaders(accessToken);

    const backendUrl = `${BACKEND_URL}/api/applications/${applicationId}/analysis/retry/`;
    const response = await fetch(backendUrl, {
      method: "POST",
      headers: {
        Authorization: headers.Authorization,
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
