import { NextRequest } from "next/server";
import { getAccessToken } from "@/lib/server/tokens";
import { getAuthHeaders } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/**
 * GET /api/organizations/:orgId/job-profiles/:jobProfileId/export/:exportId/download
 *
 * Proxy the export file download from Django, streaming the file bytes back.
 */
export async function GET(
  _request: NextRequest,
  {
    params,
  }: {
    params: Promise<{
      orgId: string;
      jobProfileId: string;
      exportId: string;
    }>;
  },
) {
  try {
    const { orgId, jobProfileId, exportId } = await params;
    const accessToken = await getAccessToken();
    if (!accessToken) {
      return new Response(JSON.stringify({ detail: "Not authenticated" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }
    const headers = getAuthHeaders(accessToken);

    const backendUrl = `${BACKEND_URL}/api/organizations/${orgId}/job-profiles/${jobProfileId}/export/${exportId}/download/`;
    const response = await fetch(backendUrl, {
      headers: { Authorization: headers.Authorization },
    });

    if (!response.ok) {
      const text = await response.text();
      return new Response(text, {
        status: response.status,
        headers: { "Content-Type": "application/json" },
      });
    }

    const blob = await response.blob();
    const contentType =
      response.headers.get("Content-Type") ?? "application/octet-stream";
    const contentDisposition =
      response.headers.get("Content-Disposition") ?? "attachment";

    return new Response(blob, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Content-Disposition": contentDisposition,
      },
    });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
