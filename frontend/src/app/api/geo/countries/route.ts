import { NextResponse } from "next/server";
import { apiGeoCountriesList } from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import { errorResponse } from "@/lib/server/errors";

/**
 * GET /api/geo/countries
 *
 * Public endpoint — returns a list of all countries with their ISO-2 codes.
 */
export async function GET() {
  try {
    const response = await apiGeoCountriesList({ client });
    return NextResponse.json(response.data);
  } catch (error) {
    return errorResponse(error);
  }
}
