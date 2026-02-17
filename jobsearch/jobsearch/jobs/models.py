from django.db import models

from django.contrib.auth.models import AbstractUser
from django.conf import settings

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


# jobs/models.py — add below RecruiterProfile

class JobPosting(models.Model):
    class JobType(models.TextChoices):
        REMOTE = "remote", "Remote"
        ONSITE = "onsite", "On-site"
        HYBRID = "hybrid", "Hybrid"

    class ExperienceLevel(models.TextChoices):
        ENTRY = "entry", "Entry Level"
        MID = "mid", "Mid Level"
        SENIOR = "senior", "Senior Level"
        INTERN = "intern", "Internship"

    recruiter = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="job_postings"
    )
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    location = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    job_type = models.CharField(
        max_length=20, choices=JobType.choices, default=JobType.ONSITE
    )
    experience_level = models.CharField(
        max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.ENTRY
    )
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    visa_sponsorship = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def skills_list(self):
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    def salary_display(self):
        if self.salary_min and self.salary_max:
            return f"${self.salary_min:,} – ${self.salary_max:,}"
        elif self.salary_min:
            return f"From ${self.salary_min:,}"
        elif self.salary_max:
            return f"Up to ${self.salary_max:,}"
        return "Not specified"

    def __str__(self):
        return f"{self.title} at {self.company}"
    
class Application(models.Model):
    job = models.ForeignKey('JobPosting', on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Meta:
    constraints = [
        models.UniqueConstraint(fields=["job", "applicant"], name="unique_application_per_job")
    ]


    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"
