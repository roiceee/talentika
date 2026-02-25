import axios, { type AxiosError } from "axios";
import type { UserProfile } from "@/types";

/**
 * Client-side auth helpers.
 *
 * These functions run in the browser and call the Next.js BFF API routes.
 * All actual Django API communication happens server-side; the browser
 * never sees or stores JWT tokens directly.
 */

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirm: string;
  invitation_token?: string;
}

/**
 * Get the CSRF token from the cookie (set by /api/auth/csrf).
 */
function getCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Create an axios instance configured for BFF API requests.
 * Automatically includes the CSRF token header on state-changing requests.
 */
const bffClient = axios.create({
  baseURL: "",
  headers: {
    "Content-Type": "application/json",
  },
});

// Add CSRF token to all state-changing requests
bffClient.interceptors.request.use((config) => {
  if (["post", "put", "patch", "delete"].includes(config.method ?? "")) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      config.headers["X-CSRF-Token"] = csrfToken;
    }
  }
  return config;
});

/**
 * Ensure a CSRF token cookie exists by calling the CSRF endpoint.
 * Should be called once on app initialization.
 */
export async function ensureCsrfToken(): Promise<void> {
  const existing = getCsrfToken();
  if (!existing) {
    await bffClient.get("/api/auth/csrf");
  }
}

/**
 * Login via the BFF. Credentials are sent to the Next.js server,
 * which proxies them to Django and stores tokens in httpOnly cookies.
 */
export async function login(credentials: LoginCredentials): Promise<void> {
  const response = await bffClient.post("/api/auth/login", credentials);

  if (!response.data.success) {
    throw new Error("Login failed");
  }
}

/**
 * Register via the BFF. Registration data is sent to the Next.js server,
 * which creates the user in Django and auto-logs them in.
 */
export async function register(data: RegisterData): Promise<void> {
  const response = await bffClient.post("/api/auth/register", data);

  if (!response.data.success) {
    throw new Error("Registration failed");
  }
}

/**
 * Logout by clearing httpOnly cookies on the server.
 */
export async function logout(): Promise<void> {
  await bffClient.post("/api/auth/logout");
}

/**
 * Get the current authenticated user's profile from the BFF.
 * Returns null if not authenticated.
 */
export async function getMe(): Promise<UserProfile | null> {
  try {
    const response = await bffClient.get("/api/auth/me");
    return response.data;
  } catch (error: unknown) {
    const axiosError = error as AxiosError;
    if (axiosError.response?.status === 401) {
      return null;
    }
    throw error;
  }
}

export { bffClient };
