from django.urls import path
from .views import (
    list_job_categories,
    list_experience_levels,
    create_job_profile,
    list_organization_job_profiles,
    get_job_profile,
    update_job_profile,
    delete_job_profile,
    delete_org_job_profile,
    list_create_org_job_categories,
    delete_org_job_category,
    list_create_org_experience_levels,
    delete_org_experience_level,
)

urlpatterns = [
    path("job-profiles/job-categories/", list_job_categories, name="list-job-categories"),
    path("job-profiles/experience-levels/", list_experience_levels, name="list-experience-levels"),
    path("job-profiles/create/", create_job_profile, name="create-job-profile"),
    path("organizations/<uuid:org_id>/job-profiles/", list_organization_job_profiles, name="list-organization-job-profiles"),
    path("job-profiles/<uuid:job_id>/", get_job_profile, name="get-job-profile"),
    path("job-profiles/<uuid:job_id>/update/", update_job_profile, name="update-job-profile"),
    path("job-profiles/<uuid:job_id>/delete/", delete_job_profile, name="delete-job-profile"),
    path("organizations/<uuid:org_id>/job-profiles/<uuid:job_id>/delete/", delete_org_job_profile, name="delete-org-job-profile"),
    path("organizations/<uuid:org_id>/job-categories/", list_create_org_job_categories, name="list-create-org-job-categories"),
    path("organizations/<uuid:org_id>/job-categories/<uuid:category_id>/", delete_org_job_category, name="delete-org-job-category"),
    path("organizations/<uuid:org_id>/experience-levels/", list_create_org_experience_levels, name="list-create-org-experience-levels"),
    path("organizations/<uuid:org_id>/experience-levels/<uuid:level_id>/", delete_org_experience_level, name="delete-org-experience-level"),
]
