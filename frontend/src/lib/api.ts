import type {
  OrganizationList,
  Organization,
  OrganizationMembership,
  OrganizationInvitation,
  JobProfileList,
  JobProfileDetail,
  JobProfileCreate,
  JobCategory,
  ExperienceLevel,
  UserProfile,
  JobApplicationCreate,
  JobApplicationDetail,
  JobApplicationDetailWithAnalysis,
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

export async function uploadUserProfilePicture(
  file: File,
): Promise<UserProfile> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await bffClient.post<UserProfile>(
    "/api/users/profile/picture",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

export async function deleteUserProfilePicture(): Promise<UserProfile> {
  const response = await bffClient.delete<UserProfile>(
    "/api/users/profile/picture",
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Organizations
// ---------------------------------------------------------------------------

export async function listOrganizations(): Promise<OrganizationList[]> {
  const response =
    await bffClient.get<OrganizationList[]>("/api/organizations");
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
  const response = await bffClient.patch(`/api/organizations/${orgId}`, data);
  return response.data;
}

export async function uploadOrgProfilePicture(
  orgId: string,
  file: File,
): Promise<Organization> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await bffClient.post<Organization>(
    `/api/organizations/${orgId}/profile-picture`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return response.data;
}

export async function deleteOrgProfilePicture(
  orgId: string,
): Promise<Organization> {
  const response = await bffClient.delete<Organization>(
    `/api/organizations/${orgId}/profile-picture`,
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
  const response = await bffClient.delete(`/api/organizations/${orgId}/leave`);
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

// ---------------------------------------------------------------------------
// Job Profiles
// ---------------------------------------------------------------------------

export async function listJobProfiles(
  orgId: string,
): Promise<JobProfileList[]> {
  const response = await bffClient.get<JobProfileList[]>(
    `/api/organizations/${orgId}/job-profiles`,
  );
  return response.data;
}

export async function getJobProfile(jobId: string): Promise<JobProfileDetail> {
  const response = await bffClient.get<JobProfileDetail>(
    `/api/job-profiles/${jobId}`,
  );
  return response.data;
}

export async function createJobProfile(
  data: JobProfileCreate,
): Promise<JobProfileDetail> {
  const response = await bffClient.post<JobProfileDetail>(
    "/api/job-profiles",
    data,
  );
  return response.data;
}

export async function updateJobProfile(
  jobId: string,
  data: Partial<JobProfileCreate>,
): Promise<JobProfileDetail> {
  const response = await bffClient.patch<JobProfileDetail>(
    `/api/job-profiles/${jobId}`,
    data,
  );
  return response.data;
}

export async function listJobCategories(): Promise<JobCategory[]> {
  const response = await bffClient.get<JobCategory[]>(
    "/api/job-profiles?type=categories",
  );
  return response.data;
}

export async function listExperienceLevels(): Promise<ExperienceLevel[]> {
  const response = await bffClient.get<ExperienceLevel[]>(
    "/api/job-profiles?type=experience-levels",
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Default Organization
// ---------------------------------------------------------------------------

export async function setDefaultOrganization(
  orgId: string | null,
): Promise<UserProfile> {
  const response = await bffClient.patch<UserProfile>(
    "/api/users/profile/default-organization",
    { default_organization: orgId },
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Job Profile Analytics
// ---------------------------------------------------------------------------

export type JobProfileAnalytics = {
  total_applications: number;
  status_breakdown: Record<string, number>;
  category_distribution: Record<string, number>;
  average_category: { key: string; label: string } | null;
  top_skills: { skill: string; count: number }[];
  top_traits: { trait: string; count: number }[];
  applications_over_time: { date: string; count: number }[];
};

export async function getJobProfileAnalytics(
  orgId: string,
  jobProfileId: string,
): Promise<JobProfileAnalytics> {
  const response = await bffClient.get<JobProfileAnalytics>(
    `/api/organizations/${orgId}/job-profiles/${jobProfileId}/analytics`,
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Org-wide Analytics
// ---------------------------------------------------------------------------

export type OrgAnalytics = {
  total_applications: number;
  total_job_profiles: { total: number; active: number; inactive: number };
  status_breakdown: Record<string, number>;
  category_distribution: Record<string, number>;
  average_category: { key: string; label: string } | null;
  top_skills: { skill: string; count: number }[];
  top_traits: { trait: string; count: number }[];
  applications_over_time: { date: string; count: number }[];
  applications_by_job_profile: {
    id: string;
    title: string;
    employment_type: string;
    is_active: boolean;
    application_count: number;
    avg_score_category: { key: string; label: string } | null;
  }[];
  employment_type_breakdown: Record<string, number>;
};

export async function getOrgAnalytics(orgId: string): Promise<OrgAnalytics> {
  const response = await bffClient.get<OrgAnalytics>(
    `/api/organizations/${orgId}/analytics`,
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Job Applications (public endpoints)
// ---------------------------------------------------------------------------

export type { JobApplicationCreate };
export type { JobApplicationDetail };

export type ApplicationListParams = {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  ordering?: string;
};

export type PaginatedApplications = {
  count: number;
  page: number;
  page_size: number;
  num_pages: number;
  results: JobApplicationDetailWithAnalysis[];
};

export async function listJobApplications(
  orgId: string,
  jobProfileId: string,
  params?: ApplicationListParams,
): Promise<PaginatedApplications> {
  const response = await bffClient.get<PaginatedApplications>(
    `/api/organizations/${orgId}/job-profiles/${jobProfileId}/applications`,
    { params },
  );
  return response.data;
}

export async function getJobApplication(
  orgId: string,
  jobProfileId: string,
  applicationId: string,
): Promise<JobApplicationDetailWithAnalysis> {
  const response = await bffClient.get<JobApplicationDetailWithAnalysis>(
    `/api/organizations/${orgId}/job-profiles/${jobProfileId}/applications/${applicationId}`,
  );
  return response.data;
}

export function getResumeDownloadUrl(
  orgId: string,
  jobProfileId: string,
  applicationId: string,
): string {
  return `/api/organizations/${orgId}/job-profiles/${jobProfileId}/applications/${applicationId}/download`;
}

export async function updateApplicationStatus(
  orgId: string,
  jobProfileId: string,
  applicationId: string,
  newStatus: "to_be_reviewed" | "reviewed" | "shortlisted" | "rejected",
): Promise<JobApplicationDetail> {
  const response = await bffClient.patch<JobApplicationDetail>(
    `/api/organizations/${orgId}/job-profiles/${jobProfileId}/applications/${applicationId}/status`,
    { status: newStatus },
  );
  return response.data;
}

export async function retryAnalysis(
  applicationId: string,
): Promise<{ detail: string; analysis_id: string }> {
  const response = await bffClient.post<{
    detail: string;
    analysis_id: string;
  }>(`/api/applications/${applicationId}/analysis/retry`);
  return response.data;
}

export async function submitApplication(
  data: JobApplicationCreate,
): Promise<JobApplicationDetail> {
  const response = await bffClient.post<JobApplicationDetail>(
    "/api/applications/submit",
    data,
  );
  return response.data;
}

export async function uploadResume(
  file: File,
): Promise<{ file_id: string; file_name: string; file_size: number }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await bffClient.post<{
    file_id: string;
    file_name: string;
    file_size: number;
  }>("/api/applications/submit/upload/resume", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

/**
 * Fetch a public job profile detail. This goes through the BFF but requires
 * no authentication — it proxies to Django's public endpoint.
 */
export async function getPublicJobProfile(
  jobId: string,
): Promise<JobProfileDetail> {
  const response = await bffClient.get<JobProfileDetail>(
    `/api/job-profiles/${jobId}`,
  );
  return response.data;
}

// ---------------------------------------------------------------------------
// Geo (public)
// ---------------------------------------------------------------------------

export interface GeoCountry {
  iso2: string;
  name: string;
  phone_code?: string;
  emoji?: string;
}

export interface GeoState {
  iso2: string;
  name: string;
}

export interface GeoCity {
  name: string;
}

export async function getCountries(): Promise<GeoCountry[]> {
  const response = await bffClient.get<GeoCountry[]>("/api/geo/countries");
  return response.data;
}

export async function getStates(countryCode: string): Promise<GeoState[]> {
  const response = await bffClient.get<GeoState[]>(
    `/api/geo/countries/${countryCode}/states`,
  );
  return response.data;
}

export async function getCities(
  countryCode: string,
  stateCode: string,
): Promise<GeoCity[]> {
  const response = await bffClient.get<GeoCity[]>(
    `/api/geo/countries/${countryCode}/states/${stateCode}/cities`,
  );
  return response.data;
}
