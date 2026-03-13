from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/seeker/", views.register_seeker, name="register_seeker"),
    path("register/recruiter/", views.register_recruiter, name="register_recruiter"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="home"), name="logout"),

    # Job search
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),

    # Apply + track
    path("jobs/<int:pk>/apply/", views.apply_to_job, name="apply_to_job"),
    path("my-applications/", views.my_applications, name="my_applications"),

    # Recruiter
    path("recruiter/dashboard/", views.recruiter_dashboard, name="recruiter_dashboard"),
    path("recruiter/jobs/new/", views.job_create, name="job_create"),
    path("recruiter/jobs/<int:pk>/edit/", views.job_edit, name="job_edit"),
    path("recruiter/jobs/<int:pk>/delete/", views.job_delete, name="job_delete"),
    path("recruiter/jobs/<int:pk>/applicants/", views.job_applicants, name="job_applicants"),
    path("recruiter/applications/<int:app_id>/status/", views.update_application_status, name="update_application_status"),
    path("recruiter/candidate/<int:user_id>/", views.view_candidate, name="view_candidate"),
    path("recruiter/candidates/", views.recruiter_candidate_search, name="recruiter_candidate_search"),
    path("recruiter/saved-searches/", views.saved_searches_list, name="saved_searches_list"),
    path("recruiter/saved-searches/<int:search_id>/delete/", views.delete_saved_search, name="delete_saved_search"),
    path("recruiter/saved-searches/<int:search_id>/mark-read/", views.mark_search_notifications_read, name="mark_search_notifications_read"),
    path("recruiter/profile/", views.recruiter_profile, name="recruiter_profile"),
    path("recruiter/profile/edit/", views.recruiter_profile_edit, name="recruiter_profile_edit"),


    # Job Seeker Profile
    path("profile/", views.seeker_profile, name="seeker_profile"),
    path("profile/edit/", views.seeker_profile_edit, name="seeker_profile_edit"),
    path("account/delete/", views.delete_account, name="delete_account"),

    # Report
    path("report/<int:user_id>/", views.report_profile, name="report_profile"),

    # Admin
    path("site-admin/users/", views.admin_user_list, name="admin_user_list"),
    path("site-admin/users/<int:user_id>/", views.admin_user_update, name="admin_user_update"),
    path("site-admin/jobs/", views.admin_job_list, name="admin_job_list"),
    path("site-admin/jobs/<int:pk>/delete/", views.admin_job_delete, name="admin_job_delete"),
    path("site-admin/reports/", views.admin_report_list, name="admin_report_list"),
    path("site-admin/reports/<int:pk>/resolve/", views.admin_report_resolve, name="admin_report_resolve"),

    # Map + Recommendations
    path("map/", views.job_map, name="job_map"),
    path("recruiter/candidate-map/", views.candidate_cluster_map, name="candidate_cluster_map"),
    path("recommended/", views.recommended_jobs, name="recommended_jobs"),
    path("recruiter/recommended/", views.recommended_candidates, name="recommended_candidates"),

    # Recruiter pipeline
    path("recruiter/pipeline/data/", views.recruiter_pipeline_data, name="recruiter_pipeline_data"),
    path("recruiter/pipeline/applications/<int:app_id>/status/", views.update_application_status_ajax, name="update_application_status_ajax"),

    path("recruiter/pipeline/", views.recruiter_pipeline, name="recruiter_pipeline"),
    path("applications/<int:pk>/status/", views.update_application_status_ajax, name="update_application_status_ajax"),
    path("api/stats/today/", views.stats_today, name="stats_today"),

    # Milestones
    path("milestones/save/", views.save_milestones, name="save_milestones"),

    path("inbox/", views.inbox, name="inbox"),
    path("inbox/<int:convo_id>/", views.conversation_detail, name="conversation_detail"),
    path("inbox/start/<int:application_id>/", views.start_conversation, name="start_conversation"),
    path("inbox/start/candidate/<int:user_id>/", views.start_conversation_with_candidate, name="start_conversation_with_candidate"),
    path("inbox/start/candidate/<int:user_id>/", views.start_conversation_with_candidate, name="start_conversation_with_candidate"),

    path("recruiter/pipeline/", views.recruiter_pipeline, name="recruiter_pipeline"),
    path("applications/<int:pk>/status/", views.update_application_status_ajax, name="update_application_status_ajax"),
    path("api/stats/today/", views.stats_today, name="stats_today"),
    ]