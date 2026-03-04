from django.urls import path
from .views import (
    list_job_categories,
    list_experience_levels,
    create_job_profile,
    list_organization_job_profiles,
    get_job_profile,
    update_job_profile,
)

urlpatterns = [
    path("job-profiles/job-categories/", list_job_categories, name="list-job-categories"),
    path("job-profiles/experience-levels/", list_experience_levels, name="list-experience-levels"),
    path("job-profiles/create/", create_job_profile, name="create-job-profile"),
    path("organizations/<uuid:org_id>/job-profiles/", list_organization_job_profiles, name="list-organization-job-profiles"),
    path("job-profiles/<uuid:job_id>/", get_job_profile, name="get-job-profile"),
    path("job-profiles/<uuid:job_id>/update/", update_job_profile, name="update-job-profile"),
]
