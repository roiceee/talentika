from django.urls import path
from .views import (
    submit_job_application,
    upload_resume,
    list_job_applications,
    get_job_application,
    delete_job_application,
    download_resume,
    update_application_status,
    job_profile_analytics,
    org_analytics,
    application_results_summary,
    request_export,
    poll_export,
    download_export,
)

urlpatterns = [
    path("applications/submit/", submit_job_application, name="submit_job_application"),
    path("applications/submit/upload/resume/", upload_resume, name="upload_resume"),
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/applications/",
        list_job_applications,
        name="list_job_applications",
    ),
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/applications/<uuid:job_application_id>/",
        get_job_application,
        name="get_job_application",
    ),
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/applications/<uuid:job_application_id>/delete/",
        delete_job_application,
        name="delete_job_application",
    ),
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/applications/<uuid:job_application_id>/download/",
        download_resume,
        name="download_resume",
    ),
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/applications/<uuid:job_application_id>/status/",
        update_application_status,
        name="update_application_status",
    ),
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/analytics/",
        job_profile_analytics,
        name="job_profile_analytics",
    ),
    path(
        "organizations/<uuid:org_id>/analytics/",
        org_analytics,
        name="org_analytics",
    ),
    # Results summary (grouped by status)
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/results/",
        application_results_summary,
        name="application_results_summary",
    ),
    # Export: request, poll, download
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/export/",
        request_export,
        name="request_export",
    ),
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/export/<uuid:export_id>/",
        poll_export,
        name="poll_export",
    ),
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/export/<uuid:export_id>/download/",
        download_export,
        name="download_export",
    ),
]
