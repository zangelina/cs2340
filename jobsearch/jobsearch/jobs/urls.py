from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Home + Auth
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

    # Job Seeker Profile
    path("profile/", views.seeker_profile, name="seeker_profile"),
    path("profile/edit/", views.seeker_profile_edit, name="seeker_profile_edit"),

    # Admin (custom pages)
    path("site-admin/users/", views.admin_user_list, name="admin_user_list"),
    path("site-admin/users/<int:user_id>/", views.admin_user_update, name="admin_user_update"),
    path("site-admin/jobs/", views.admin_job_list, name="admin_job_list"),
    path("site-admin/jobs/<int:pk>/delete/", views.admin_job_delete, name="admin_job_delete"),

    # Map
    path("map/", views.job_map, name="job_map"),

    # Recommendations
    path("recommended/", views.recommended_jobs, name="recommended_jobs"),
]