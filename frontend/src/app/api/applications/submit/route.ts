import { NextRequest, NextResponse } from "next/server";
import { apiApplicationsSubmitCreate } from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/applications/submit
 *
 * Submit a job application (public — no authentication required).
 * Proxies directly to the Django backend.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await apiApplicationsSubmitCreate({
      client,
      body,
    });
    return NextResponse.json(response.data, { status: 201 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
