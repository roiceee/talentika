import { NextRequest, NextResponse } from "next/server";
import { getAccessToken } from "@/lib/server/tokens";
import { getAuthHeaders } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/**
 * PATCH /api/organizations/:orgId/job-profiles/:jobProfileId/applications/:applicationId/status
 *
 * Update the status of a job application.
 */
export async function PATCH(
  request: NextRequest,
  {
    params,
  }: {
    params: Promise<{
      orgId: string;
      jobProfileId: string;
      applicationId: string;
    }>;
  },
) {
  try {
    const { orgId, jobProfileId, applicationId } = await params;
    const accessToken = await getAccessToken();
    if (!accessToken) {
      return NextResponse.json(
        { detail: "Not authenticated" },
        { status: 401 },
      );
    }
    const headers = getAuthHeaders(accessToken);
    const body = await request.json();

    const backendUrl = `${BACKEND_URL}/api/organizations/${orgId}/job-profiles/${jobProfileId}/applications/${applicationId}/status/`;
    const response = await fetch(backendUrl, {
      method: "PATCH",
      headers: {
        Authorization: headers.Authorization,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
