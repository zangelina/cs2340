from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/seeker/", views.register_seeker, name="register_seeker"),
    path("register/recruiter/", views.register_recruiter, name="register_recruiter"),
    path("login/", LoginView.as_view(template_name="jobs/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="home"), name="logout"),
]