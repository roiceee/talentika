from django.urls import path

from . import views

urlpatterns = [
    # Test endpoint — OCR extraction without DB / queue
    path(
        "test-resume-extraction/",
        views.test_resume_extraction,
        name="test-resume-extraction",
    ),
    # List all analyses for an org (filterable & sortable)
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/analyses/",
        views.list_analyses,
        name="list-analyses",
    ),
    # Full analysis result for a specific application
    path(
        "applications/<uuid:application_id>/analysis/",
        views.get_analysis,
        name="get-analysis",
    ),
    # Re-trigger a failed analysis
    path(
        "applications/<uuid:application_id>/analysis/retry/",
        views.retry_analysis,
        name="retry-analysis",
    ),
]
