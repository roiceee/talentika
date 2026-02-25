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
 * These provide convenience wrappers around the BFF proxy for
 * common API operations. All requests go through the Next.js
 * server-side proxy which handles authentication.
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
  // TODO: dedicated BFF route needed
  throw new Error(
    `updateUserProfile not yet implemented via BFF: ${JSON.stringify(data)}`,
  );
}

// ---------------------------------------------------------------------------
// Organizations
// ---------------------------------------------------------------------------

export async function listOrganizations(): Promise<OrganizationList[]> {
  // TODO: dedicated BFF route needed
  throw new Error("listOrganizations not yet implemented via BFF");
}

export async function createOrganization(data: {
  name: string;
  description?: string | null;
}): Promise<unknown> {
  // TODO: dedicated BFF route needed
  throw new Error(
    `createOrganization not yet implemented via BFF: ${JSON.stringify(data)}`,
  );
}

export async function getOrganization(orgId: string): Promise<Organization> {
  // TODO: dedicated BFF route needed
  throw new Error(`getOrganization not yet implemented via BFF: ${orgId}`);
}

export async function updateOrganization(
  orgId: string,
  data: { name?: string; description?: string },
): Promise<unknown> {
  // TODO: dedicated BFF route needed
  throw new Error(
    `updateOrganization not yet implemented via BFF: ${orgId}, ${JSON.stringify(data)}`,
  );
}

// ---------------------------------------------------------------------------
// Members
// ---------------------------------------------------------------------------

export async function listMembers(
  orgId: string,
): Promise<OrganizationMembership[]> {
  // TODO: dedicated BFF route needed
  throw new Error(`listMembers not yet implemented via BFF: ${orgId}`);
}

export async function removeMember(
  orgId: string,
  membershipId: string,
): Promise<unknown> {
  // TODO: dedicated BFF route needed
  throw new Error(
    `removeMember not yet implemented via BFF: ${orgId}, ${membershipId}`,
  );
}

export async function leaveOrganization(orgId: string): Promise<unknown> {
  // TODO: dedicated BFF route needed
  throw new Error(`leaveOrganization not yet implemented via BFF: ${orgId}`);
}

// ---------------------------------------------------------------------------
// Invitations
// ---------------------------------------------------------------------------

export async function listInvitations(
  orgId: string,
): Promise<OrganizationInvitation[]> {
  // TODO: dedicated BFF route needed
  throw new Error(`listInvitations not yet implemented via BFF: ${orgId}`);
}

export async function createInvitation(
  orgId: string,
  data: { email: string; role: string },
): Promise<{ email_sent?: boolean }> {
  // TODO: dedicated BFF route needed
  throw new Error(
    `createInvitation not yet implemented via BFF: ${orgId}, ${JSON.stringify(data)}`,
  );
}

export async function validateInvitation(
  token: string,
): Promise<InvitationValidationResult> {
  // TODO: dedicated BFF route needed
  throw new Error(`validateInvitation not yet implemented via BFF: ${token}`);
}

export async function acceptInvitation(token: string): Promise<unknown> {
  // TODO: dedicated BFF route needed
  throw new Error(`acceptInvitation not yet implemented via BFF: ${token}`);
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
