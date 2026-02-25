from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# ── Custom User ───────────────────────────────────────

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


# ── Job Seeker Profile ────────────────────────────────

class JobSeekerProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="seeker_profile"
    )

    # Identity
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    headline = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True, help_text="Short summary about yourself")
    location = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)

    # Professional
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)
    projects = models.TextField(blank=True, help_text="Key projects, coursework, open-source contributions")
    certifications = models.TextField(blank=True, help_text="Certifications, licenses, awards")
    languages = models.TextField(blank=True, help_text="Spoken languages, e.g. English (Native), Spanish (Conversational)")
    links = models.TextField(blank=True, help_text="GitHub, LinkedIn, portfolio URLs (one per line)")

    # Featured showcase
    featured_label = models.CharField(
        max_length=100, blank=True,
        help_text="Label shown above the embed, e.g. 'My Portfolio', 'Intro Video'"
    )
    featured_url = models.URLField(
        blank=True,
        help_text="Link to a website, portfolio, or project (displayed as a clickable card)"
    )
    featured_video_url = models.URLField(
        blank=True,
        help_text="YouTube or Vimeo link for an introduction / project video"
    )

    # Preferences
    desired_job_title = models.CharField(max_length=200, blank=True)
    desired_salary_min = models.PositiveIntegerField(null=True, blank=True)
    open_to_remote = models.BooleanField(default=True)
    open_to_relocation = models.BooleanField(default=False)
    visa_required = models.BooleanField(default=False)

    class DistanceUnit(models.TextChoices):
        MILES = "mi", "Miles"
        KM = "km", "Kilometers"

    commute_distance = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Maximum commute distance"
    )
    distance_unit = models.CharField(
        max_length=2, choices=DistanceUnit.choices, default=DistanceUnit.MILES
    )

    # Privacy toggles
    is_public = models.BooleanField(default=True)
    show_photo = models.BooleanField(default=True)
    show_headline = models.BooleanField(default=True)
    show_bio = models.BooleanField(default=True)
    show_skills = models.BooleanField(default=True)
    show_education = models.BooleanField(default=True)
    show_experience = models.BooleanField(default=True)
    show_projects = models.BooleanField(default=True)
    show_certifications = models.BooleanField(default=True)
    show_languages = models.BooleanField(default=True)
    show_links = models.BooleanField(default=True)
    show_location = models.BooleanField(default=True)
    show_phone = models.BooleanField(default=False)
    show_email = models.BooleanField(default=True)
    show_featured = models.BooleanField(default=True)

    def skills_list(self):
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    def is_complete(self):
        return all([
            self.user.first_name,
            self.user.last_name,
            self.headline,
            self.skills.strip(),
        ])

    def completion_missing(self):
        missing = []
        if not self.user.first_name:
            missing.append("First name")
        if not self.user.last_name:
            missing.append("Last name")
        if not self.headline:
            missing.append("Headline")
        if not self.skills.strip():
            missing.append("At least one skill")
        return missing

    def has_featured(self):
        return bool(self.featured_url or self.featured_video_url)

    def video_embed_url(self):
        """Convert YouTube/Vimeo watch URLs to embeddable URLs."""
        url = self.featured_video_url
        if not url:
            return ""
        # YouTube
        if "youtube.com/watch" in url:
            vid = url.split("v=")[-1].split("&")[0]
            return f"https://www.youtube.com/embed/{vid}"
        if "youtu.be/" in url:
            vid = url.split("youtu.be/")[-1].split("?")[0]
            return f"https://www.youtube.com/embed/{vid}"
        # Vimeo
        if "vimeo.com/" in url:
            vid = url.strip("/").split("/")[-1]
            return f"https://player.vimeo.com/video/{vid}"
        return url

    def __str__(self):
        return f"{self.user.username} — Seeker Profile"


# ── Recruiter Profile ─────────────────────────────────

class RecruiterProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="recruiter_profile"
    )
    company_name = models.CharField(max_length=200)
    company_website = models.URLField(blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} — {self.company_name}"


# ── Job Posting ───────────────────────────────────────

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


# ── Application ───────────────────────────────────────

class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        REVIEW = "review", "In Review"
        INTERVIEW = "interview", "Interview"
        OFFER = "offer", "Offer"
        CLOSED = "closed", "Closed"

    job = models.ForeignKey(
        JobPosting, on_delete=models.CASCADE, related_name="applications"
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    note = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.APPLIED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job", "applicant"], name="unique_application_per_job"
            )
        ]

    def __str__(self):
        return f"{self.applicant.username} → {self.job.title}"


# ── Profile Report ────────────────────────────────────

class ProfileReport(models.Model):
    class Reason(models.TextChoices):
        INAPPROPRIATE = "inappropriate", "Inappropriate or offensive content"
        SPAM = "spam", "Spam or misleading links"
        IMPERSONATION = "impersonation", "Impersonation"
        HARMFUL = "harmful", "Harmful or dangerous content"
        OTHER = "other", "Other"

    profile = models.ForeignKey(
        JobSeekerProfile, on_delete=models.CASCADE, related_name="reports"
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="filed_reports"
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True, help_text="Optional additional context")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report on {self.profile.user.username} by {self.reported_by.username}"