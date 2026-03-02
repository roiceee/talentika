import { NextRequest, NextResponse } from "next/server";
import { apiApplicationsSubmitUploadResumeCreate } from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/applications/submit/upload/resume
 *
 * Pre-upload a resume to temporary storage (public — no auth required).
 * Accepts multipart/form-data with a single `file` field.
 * Returns { file_id, file_name, file_size }.
 */
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    const response = await apiApplicationsSubmitUploadResumeCreate({
      client,
      body: { file },
    });

    return NextResponse.json(response.data, { status: 201 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
