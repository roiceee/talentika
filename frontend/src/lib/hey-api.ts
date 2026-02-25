import type { CreateClientConfig } from "./client/client.gen";

/**
 * Runtime configuration for the hey-api generated client.
 *
 * This is used server-side only (in Next.js API routes) to point
 * the generated client at the Django REST API backend.
 *
 * The `runtimeConfigPath` in openapi-ts.config.ts references this file.
 */
export const createClientConfig: CreateClientConfig = (override) => ({
  baseURL: process.env.BACKEND_URL || "http://localhost:8000/",
  ...override,
});
