import { NextRequest, NextResponse } from "next/server";
import {
  apiJobProfilesCreateCreate,
  apiJobProfilesJobCategoriesList,
  apiJobProfilesExperienceLevelsList,
} from "@/lib/client";
import { authenticatedSdkCall } from "@/lib/server/api-client";
import { errorResponse } from "@/lib/server/errors";

/**
 * POST /api/job-profiles
 *
 * Create a new job profile.
 * Only organization admins can create job profiles.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const response = await authenticatedSdkCall((opts) =>
      apiJobProfilesCreateCreate({ ...opts, body }),
    );
    return NextResponse.json(response.data, { status: 201 });
  } catch (error: unknown) {
    return errorResponse(error);
  }
}

/**
 * GET /api/job-profiles?type=categories|experience-levels
 *
 * Get reference data for job profile creation.
 * Query param `type` determines which reference data to return.
 */
export async function GET(request: NextRequest) {
  try {
    const type = request.nextUrl.searchParams.get("type");

    if (type === "categories") {
      const response = await authenticatedSdkCall((opts) =>
        apiJobProfilesJobCategoriesList({ ...opts }),
      );
      return NextResponse.json(response.data);
    }

    if (type === "experience-levels") {
      const response = await authenticatedSdkCall((opts) =>
        apiJobProfilesExperienceLevelsList({ ...opts }),
      );
      return NextResponse.json(response.data);
    }

    return NextResponse.json(
      {
        error:
          "Missing or invalid 'type' query parameter. Use: categories or experience-levels",
      },
      { status: 400 },
    );
  } catch (error: unknown) {
    return errorResponse(error);
  }
}
