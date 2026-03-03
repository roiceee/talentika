import { NextRequest } from "next/server";
import { getAccessToken } from "@/lib/server/tokens";
import { getAuthHeaders } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/**
 * GET /api/organizations/:orgId/job-profiles/:jobProfileId/applications/:applicationId/download
 *
 * Proxy the resume download from Django, streaming the file bytes back to the client.
 */
export async function GET(
  _request: NextRequest,
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
      return new Response(JSON.stringify({ detail: "Not authenticated" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }
    const headers = getAuthHeaders(accessToken);

    const backendUrl = `${BACKEND_URL}/api/organizations/${orgId}/job-profiles/${jobProfileId}/applications/${applicationId}/download/`;
    const response = await fetch(backendUrl, {
      headers: {
        Authorization: headers.Authorization,
      },
    });

    if (!response.ok) {
      return new Response(
        JSON.stringify({ detail: "Failed to download resume." }),
        {
          status: response.status,
          headers: { "Content-Type": "application/json" },
        },
      );
    }

    const blob = await response.blob();
    const contentType =
      response.headers.get("Content-Type") ?? "application/octet-stream";

    return new Response(blob, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Content-Disposition": "inline",
      },
    });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
