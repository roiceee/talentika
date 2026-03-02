import { NextResponse } from "next/server";
import { apiGeoCountriesStatesList } from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/geo/countries/[countryCode]/states
 *
 * Public endpoint — returns states/provinces for the given ISO-2 country code.
 */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ countryCode: string }> },
) {
  try {
    const { countryCode } = await params;
    const response = await apiGeoCountriesStatesList({
      client,
      path: { country_code: countryCode },
    });
    return NextResponse.json(response.data);
  } catch (error) {
    return errorResponse(error);
  }
}
