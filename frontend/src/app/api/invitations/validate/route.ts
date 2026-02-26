import { NextRequest, NextResponse } from "next/server";
import { apiInvitationsValidateCreate } from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/invitations/validate
 *
 * Validate an invitation token without accepting it.
 * This is a public endpoint (no authentication required).
 *
 * Request body: { token: string }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await apiInvitationsValidateCreate({
      client,
      body,
    });
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
