import { NextRequest, NextResponse } from "next/server";
import {
  apiOrganizationsProfilePictureCreate,
  apiOrganizationsProfilePictureDeleteDelete,
} from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/organizations/[orgId]/profile-picture
 *
 * Upload or replace an organization's profile picture (admin only).
 * Accepts multipart/form-data with a single `file` field.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  try {
    const { orgId } = await params;
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsProfilePictureCreate({
        ...opts,
        body: { file },
        path: { org_id: orgId },
      }),
    );

    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}

/**
 * DELETE /api/organizations/[orgId]/profile-picture
 *
 * Remove an organization's profile picture (admin only).
 */
export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  try {
    const { orgId } = await params;
    const response = await authenticatedSdkCall((opts) =>
      apiOrganizationsProfilePictureDeleteDelete({
        ...opts,
        path: { org_id: orgId },
      }),
    );

    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
