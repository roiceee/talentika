import { NextRequest, NextResponse } from "next/server";
import {
  apiOrganizationsList,
  apiOrganizationsCreateCreate,
} from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/organizations
 *
 * List all organizations the authenticated user belongs to.
 */
export async function GET() {
  try {
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsList({ ...opts }),
    );
    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}

/**
 * POST /api/organizations
 *
 * Create a new organization. The authenticated user becomes the admin.
 *
 * Request body: { name: string, description?: string }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsCreateCreate({ ...opts, body }),
    );
    return NextResponse.json(response.data, { status: 201 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
