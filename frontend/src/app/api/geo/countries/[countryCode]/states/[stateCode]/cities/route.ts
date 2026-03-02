import { NextResponse } from "next/server";
import { apiGeoCountriesStatesCitiesList } from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/geo/countries/[countryCode]/states/[stateCode]/cities
 *
 * Public endpoint — returns cities for the given country + state.
 */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ countryCode: string; stateCode: string }> },
) {
  try {
    const { countryCode, stateCode } = await params;
    const response = await apiGeoCountriesStatesCitiesList({
      client,
      path: { country_code: countryCode, state_code: stateCode },
    });
    return NextResponse.json(response.data);
  } catch (error) {
    return errorResponse(error);
  }
}
