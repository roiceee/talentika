import { NextResponse } from "next/server";

/**
 * Shared error-handling utilities for BFF API routes.
 */

interface AxiosLikeError {
  response: {
    status: number;
    data: unknown;
  };
}

/**
 * Type guard for Axios errors that have a response body.
 */
export function isAxiosError(error: unknown): error is AxiosLikeError {
  return (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof (error as { response: unknown }).response === "object" &&
    (error as { response: unknown }).response !== null &&
    "status" in (error as { response: object }).response &&
    "data" in (error as { response: object }).response
  );
}

/**
 * Convert any caught error into a NextResponse, preserving the full Django
 * error body and status code so the client has enough context to act on it.
 *
 * Priority:
 *   1. Axios error with a response → forward Django's status + body verbatim
 *   2. Plain Error → forward the message
 *   3. Anything else → 500 with a serialised representation
 */
export function errorResponse(error: unknown): NextResponse {
  if (isAxiosError(error)) {
    return NextResponse.json(error.response.data, {
      status: error.response.status,
    });
  }

  if (error instanceof Error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(
    { error: "An unexpected error occurred", detail: String(error) },
    { status: 500 },
  );
}
