import { NextRequest, NextResponse } from "next/server";
import {
  apiUsersProfilePictureCreate,
  apiUsersProfilePictureDeleteDelete,
} from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/users/profile/picture
 *
 * Upload or replace the current user's profile picture.
 * Accepts multipart/form-data with a single `file` field.
 */
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    const response = await authenticatedSdkCall((opts) =>
      apiUsersProfilePictureCreate({ ...opts, body: { file } }),
    );

    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}

/**
 * DELETE /api/users/profile/picture
 *
 * Remove the current user's profile picture.
 */
export async function DELETE() {
  try {
    const response = await authenticatedSdkCall((opts) =>
      apiUsersProfilePictureDeleteDelete({ ...opts }),
    );

    return NextResponse.json(response.data);
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
