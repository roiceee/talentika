import { cookies } from "next/headers";

/**
 * Server-side token management using httpOnly cookies.
 *
 * Tokens are stored in httpOnly, secure (in production), sameSite=lax cookies
 * so they are never accessible to client-side JavaScript.
 */

const ACCESS_TOKEN_COOKIE = "access_token";
const REFRESH_TOKEN_COOKIE = "refresh_token";

const isProduction = process.env.NODE_ENV === "production";

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: isProduction,
  sameSite: "lax" as const,
  path: "/",
};

/**
 * Store both access and refresh JWT tokens in httpOnly cookies.
 */
export async function setTokens(accessToken: string, refreshToken: string) {
  const cookieStore = await cookies();

  cookieStore.set(ACCESS_TOKEN_COOKIE, accessToken, {
    ...COOKIE_OPTIONS,
    maxAge: 60 * 60, // 1 hour (matches Django JWT access token lifetime)
  });

  cookieStore.set(REFRESH_TOKEN_COOKIE, refreshToken, {
    ...COOKIE_OPTIONS,
    maxAge: 7 * 24 * 60 * 60, // 7 days (matches Django JWT refresh token lifetime)
  });
}

/**
 * Get the current access token from cookies.
 */
export async function getAccessToken(): Promise<string | undefined> {
  const cookieStore = await cookies();
  return cookieStore.get(ACCESS_TOKEN_COOKIE)?.value;
}

/**
 * Get the current refresh token from cookies.
 */
export async function getRefreshToken(): Promise<string | undefined> {
  const cookieStore = await cookies();
  return cookieStore.get(REFRESH_TOKEN_COOKIE)?.value;
}

/**
 * Clear all auth tokens (used on logout).
 */
export async function clearTokens() {
  const cookieStore = await cookies();
  cookieStore.delete(ACCESS_TOKEN_COOKIE);
  cookieStore.delete(REFRESH_TOKEN_COOKIE);
}
