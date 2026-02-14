# jobs/urls.py — replace entire file

from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
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

    # Recruiter
    path("recruiter/dashboard/", views.recruiter_dashboard, name="recruiter_dashboard"),
    path("recruiter/jobs/new/", views.job_create, name="job_create"),
    path("recruiter/jobs/<int:pk>/edit/", views.job_edit, name="job_edit"),
    path("recruiter/jobs/<int:pk>/delete/", views.job_delete, name="job_delete"),
]