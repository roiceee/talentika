import type {
  OrganizationList,
  Organization,
  OrganizationMembership,
  OrganizationInvitation,
} from "@/lib/client";
import { bffClient } from "@/lib/auth";

/**
 * Client-side API helpers and types.
 *
 * These provide convenience wrappers around the BFF routes for
 * common API operations. All requests go through the Next.js
 * server-side routes which handle authentication via httpOnly cookies.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/**
 * Result type for invitation validation.
 */
export interface InvitationValidationResult {
  valid: boolean;
  organization_name?: string;
  organization_id?: string;
  role?: string;
  email?: string;
  invited_by?: string;
  error?: string;
}

// ---------------------------------------------------------------------------
// User Profile
// ---------------------------------------------------------------------------

export async function updateUserProfile(data: {
  username?: string;
  first_name?: string;
  last_name?: string;
}): Promise<unknown> {
  const response = await bffClient.patch("/api/users/profile", data);
  return response.data;
}

// ---------------------------------------------------------------------------
// Organizations
// ---------------------------------------------------------------------------

export async function listOrganizations(): Promise<OrganizationList[]> {
  const response = await bffClient.get<OrganizationList[]>(
    "/api/organizations",
  );
  return response.data;
}

export async function createOrganization(data: {
  name: string;
  description?: string | null;
}): Promise<unknown> {
  const response = await bffClient.post("/api/organizations", data);
  return response.data;
}

export async function getOrganization(orgId: string): Promise<Organization> {
  const response = await bffClient.get<Organization>(
    `/api/organizations/${orgId}`,
  );
  return response.data;
}

export async function updateOrganization(
  orgId: string,
  data: { name?: string; description?: string },
): Promise<unknown> {
  const response = await bffClient.patch(
    `/api/organizations/${orgId}`,
    data,
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Members
// ---------------------------------------------------------------------------

export async function listMembers(
  orgId: string,
): Promise<OrganizationMembership[]> {
  const response = await bffClient.get<OrganizationMembership[]>(
    `/api/organizations/${orgId}/members`,
  );
  return response.data;
}

export async function removeMember(
  orgId: string,
  membershipId: string,
): Promise<unknown> {
  const response = await bffClient.delete(
    `/api/organizations/${orgId}/members/${membershipId}`,
  );
  return response.data;
}

export async function leaveOrganization(orgId: string): Promise<unknown> {
  const response = await bffClient.delete(
    `/api/organizations/${orgId}/leave`,
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Invitations
// ---------------------------------------------------------------------------

export async function listInvitations(
  orgId: string,
): Promise<OrganizationInvitation[]> {
  const response = await bffClient.get<OrganizationInvitation[]>(
    `/api/organizations/${orgId}/invitations`,
  );
  return response.data;
}

export async function createInvitation(
  orgId: string,
  data: { email: string; role: string },
): Promise<{ email_sent?: boolean }> {
  const response = await bffClient.post<{ email_sent?: boolean }>(
    `/api/organizations/${orgId}/invitations`,
    data,
  );
  return response.data;
}

export async function validateInvitation(
  token: string,
): Promise<InvitationValidationResult> {
  const response = await bffClient.post<InvitationValidationResult>(
    "/api/invitations/validate",
    { token },
  );
  return response.data;
}

export async function acceptInvitation(token: string): Promise<unknown> {
  const response = await bffClient.post("/api/invitations/accept", { token });
  return response.data;
}

// ---------------------------------------------------------------------------
// Password Reset — dedicated BFF routes → SDK → Django
// ---------------------------------------------------------------------------

export async function requestPasswordReset(
  email: string,
): Promise<{ message?: string }> {
  const response = await bffClient.post<{ message?: string }>(
    "/api/users/password-reset",
    { email },
  );
  return response.data;
}

export async function confirmPasswordReset(
  token: string,
  newPassword: string,
  confirmPassword: string,
): Promise<{ message?: string }> {
  const response = await bffClient.post<{ message?: string }>(
    "/api/users/password-reset/confirm",
    {
      token,
      new_password: newPassword,
      new_password_confirm: confirmPassword,
    },
  );
  return response.data;
}
