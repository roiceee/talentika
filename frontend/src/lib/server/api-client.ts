import {
  apiUsersAuthTokenRefreshCreate,
  apiUsersProfileList,
} from "@/lib/client";
import { client } from "@/lib/client/client.gen";
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from "./tokens";

/**
 * Server-side authenticated API client utilities.
 *
 * Provides helpers to make authenticated requests to the Django backend
 * using the hey-api generated client, with automatic token refresh on 401.
 */

/**
 * Create a client configuration with the current access token.
 * Use this to pass `client` option to SDK functions for authenticated requests.
 */
export function getAuthHeaders(accessToken: string) {
  return {
    Authorization: `Bearer ${accessToken}`,
  };
}

/**
 * Attempt to refresh the access token using the stored refresh token.
 * Returns the new access token if successful, or null if refresh fails.
 */
export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const response = await apiUsersAuthTokenRefreshCreate({
      client,
      body: { refresh: refreshToken },
    });

    if (response.data?.access && response.data?.refresh) {
      await setTokens(response.data.access, response.data.refresh);
      return response.data.access;
    }

    // If refresh failed, clear stale tokens
    await clearTokens();
    return null;
  } catch {
    await clearTokens();
    return null;
  }
}

/**
 * Get the current user profile, with automatic token refresh on 401.
 * Returns the user profile data or null if not authenticated.
 */
export async function getAuthenticatedUser() {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    return null;
  }

  try {
    const response = await apiUsersProfileList({
      client,
      headers: getAuthHeaders(accessToken),
    });

    if (response.data) {
      return response.data;
    }

    return null;
  } catch (error: unknown) {
    // Check if it's a 401 - try to refresh
    if (isUnauthorizedError(error)) {
      const newAccessToken = await refreshAccessToken();
      if (!newAccessToken) {
        return null;
      }

      try {
        const retryResponse = await apiUsersProfileList({
          client,
          headers: getAuthHeaders(newAccessToken),
        });
        return retryResponse.data ?? null;
      } catch {
        return null;
      }
    }
    return null;
  }
}

/**
 * Check if an error is a 401 Unauthorized error (from Axios).
 */
export function isUnauthorizedError(error: unknown): boolean {
  if (
    error &&
    typeof error === "object" &&
    "response" in error &&
    error.response &&
    typeof error.response === "object" &&
    "status" in error.response
  ) {
    return error.response.status === 401;
  }
  return false;
}

/**
 * Execute an authenticated SDK call with automatic 401 token refresh & retry.
 *
 * @param sdkCall  A function that receives `{ client, headers }` and returns
 *                 the SDK response. The caller should invoke the desired SDK
 *                 function inside.
 *
 * @example
 * ```ts
 * const response = await authenticatedSdkCall((opts) =>
 *   apiOrganizationsList({ ...opts }),
 * );
 * ```
 */
export async function authenticatedSdkCall<T>(
  sdkCall: (opts: {
    client: typeof client;
    headers: Record<string, string>;
  }) => Promise<T>,
): Promise<T> {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    throw new Error("Not authenticated");
  }

  try {
    return await sdkCall({
      client,
      headers: getAuthHeaders(accessToken),
    });
  } catch (error: unknown) {
    if (isUnauthorizedError(error)) {
      const newAccessToken = await refreshAccessToken();
      if (!newAccessToken) {
        throw error; // re-throw original – let the route's errorResponse handle it
      }
      return await sdkCall({
        client,
        headers: getAuthHeaders(newAccessToken),
      });
    }
    throw error;
  }
}
