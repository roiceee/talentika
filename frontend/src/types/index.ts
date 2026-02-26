/**
 * Re-export all types from the generated client.
 * Pages and components should import from here or directly from "@/lib/client".
 */
export type {
  User,
  UserProfile,
  UserUpdate,
  UserBasic,
  Organization,
  OrganizationList,
  OrganizationCreate,
  OrganizationMembership,
  OrganizationInvitation,
  InvitationCreate,
  InvitationValidate,
  Address,
  PasswordResetRequest,
  PasswordResetConfirm,
  JobProfileList,
  JobProfileDetail,
  JobProfileCreate,
  JobCategory,
  ExperienceLevel,
  AiScreeningConfiguration,
  Question,
} from "@/lib/client";

export type { InvitationValidationResult } from "@/lib/api";

// Backwards-compatible aliases
import type {
  OrganizationList,
  OrganizationCreate,
  InvitationCreate,
} from "@/lib/client";
export type OrganizationListItem = OrganizationList;
export type OrganizationCreateData = OrganizationCreate;
export type InvitationCreateData = InvitationCreate;
export type MemberRole = "ORG_ADMIN" | "MEMBER";
