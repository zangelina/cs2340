from django.db import models

from django.contrib.auth.models import AbstractUser

## for custom users
class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        JOB_SEEKER = "job_seeker", "Job Seeker"
        RECRUITER = "recruiter", "Recruiter"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.JOB_SEEKER,
    )

    def is_job_seeker(self):
        return self.role == self.Role.JOB_SEEKER

    def is_recruiter(self):
        return self.role == self.Role.RECRUITER

    def is_admin_user(self):
        return self.role == self.Role.ADMIN

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
## end custom user block


#recruiter
class JobSeekerProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="seeker_profile"
    )
    headline = models.CharField(max_length=200, blank=True)
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)
    links = models.TextField(blank=True, help_text="Portfolio, GitHub, LinkedIn, etc.")
    location = models.CharField(max_length=200, blank=True)
    is_public = models.BooleanField(default=True)

    def skills_list(self):
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    def __str__(self):
        return f"{self.user.username} — Seeker Profile"


class RecruiterProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="recruiter_profile"
    )
    company_name = models.CharField(max_length=200)
    company_website = models.URLField(blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} — {self.company_name}"
##