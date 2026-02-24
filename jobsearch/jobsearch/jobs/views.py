from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
import re

from .forms import (
    JobSeekerRegistrationForm,
    RecruiterRegistrationForm,
    JobPostingForm,
    JobSeekerProfileForm,
    ApplicationForm,
)
from .models import CustomUser, JobPosting, JobSeekerProfile, Application


# ── Admin guard ────────────────────────────────────────

def is_admin_user(user):
    return user.is_authenticated and user.is_staff


admin_required = user_passes_test(is_admin_user)


# ── Home ───────────────────────────────────────────────

def home(request):
    jobs = JobPosting.objects.filter(is_active=True)[:6]
    return render(request, "jobs/home.html", {"jobs": jobs})


# ── Custom login redirect ──────────────────────────────

class CustomLoginView(LoginView):
    template_name = "jobs/login.html"

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, "is_recruiter") and user.is_recruiter():
            return reverse_lazy("recruiter_dashboard")
        if hasattr(user, "is_job_seeker") and user.is_job_seeker():
            return reverse_lazy("home")
        return reverse_lazy("home")


# ── Auth ──────────────────────────────────────────────

def register_seeker(request):
    if request.method == "POST":
        form = JobSeekerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = JobSeekerRegistrationForm()
    return render(request, "jobs/register.html", {"form": form, "role": "Job Seeker"})


def register_recruiter(request):
    if request.method == "POST":
        form = RecruiterRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = RecruiterRegistrationForm()
    return render(request, "jobs/register.html", {"form": form, "role": "Recruiter"})


def job_map(request):
    jobs = JobPosting.objects.filter(
        is_active=True,
        latitude__isnull=False,
        longitude__isnull=False
    )
    return render(request, "jobs/job_map.html", {"jobs": jobs})


# ── Job Search ────────────────────────────────────────

def job_list(request):
    jobs = JobPosting.objects.filter(is_active=True)

    q = request.GET.get("q", "").strip()
    location = request.GET.get("location", "").strip()
    job_type = request.GET.get("job_type", "")
    experience = request.GET.get("experience", "")
    visa = request.GET.get("visa", "")
    salary_min = request.GET.get("salary_min", "")

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) | Q(skills__icontains=q) | Q(company__icontains=q)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if experience:
        jobs = jobs.filter(experience_level=experience)
    if visa:
        jobs = jobs.filter(visa_sponsorship=True)
    if salary_min:
        try:
            jobs = jobs.filter(salary_max__gte=int(salary_min))
        except ValueError:
            pass

    context = {
        "jobs": jobs,
        "q": q,
        "location": location,
        "job_type": job_type,
        "experience": experience,
        "visa": visa,
        "salary_min": salary_min,
        "job_type_choices": JobPosting.JobType.choices,
        "experience_choices": JobPosting.ExperienceLevel.choices,
    }
    return render(request, "jobs/job_list.html", context)


def job_detail(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    already_applied = False
    if request.user.is_authenticated and request.user.is_job_seeker():
        already_applied = Application.objects.filter(
            job=job, applicant=request.user
        ).exists()
    return render(request, "jobs/job_detail.html", {
        "job": job,
        "already_applied": already_applied,
    })


# ── Apply to job ───────────────────────────────────────

@login_required
def apply_to_job(request, pk):
    if not request.user.is_job_seeker():
        return redirect("home")

    job = get_object_or_404(JobPosting, pk=pk)

    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, "You already applied to this job.")
        return redirect("job_detail", pk=pk)

    if request.method == "POST":
        form = ApplicationForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            app.job = job
            app.applicant = request.user
            app.save()
            messages.success(request, "Application submitted!")
            return redirect("my_applications")
    else:
        form = ApplicationForm()

    return render(request, "jobs/apply.html", {"job": job, "form": form})


# ── My Applications (job seeker tracker — user story 4) ──

@login_required
def my_applications(request):
    if not request.user.is_job_seeker():
        return redirect("home")
    apps = Application.objects.filter(applicant=request.user).select_related("job").order_by("-created_at")
    return render(request, "jobs/my_applications.html", {"applications": apps})


# ── Recruiter CRUD ────────────────────────────────────

@login_required
def recruiter_dashboard(request):
    if not request.user.is_recruiter():
        return redirect("home")
    jobs = JobPosting.objects.filter(recruiter=request.user).order_by("-created_at")
    return render(request, "jobs/recruiter_dashboard.html", {"jobs": jobs})


@login_required
def job_create(request):
    if not request.user.is_recruiter():
        return redirect("home")

    if request.method == "POST":
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.save()
            messages.success(request, "Job posted!")
            return redirect("recruiter_dashboard")
    else:
        form = JobPostingForm()

    return render(request, "jobs/job_form.html", {"form": form, "mode": "create"})


@login_required
def job_edit(request, pk):
    if not request.user.is_recruiter():
        return redirect("home")

    job = get_object_or_404(JobPosting, pk=pk, recruiter=request.user)

    if request.method == "POST":
        form = JobPostingForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect("recruiter_dashboard")
    else:
        form = JobPostingForm(instance=job)

    return render(request, "jobs/job_form.html", {"form": form, "mode": "edit", "job": job})


@login_required
def job_delete(request, pk):
    if not request.user.is_recruiter():
        return redirect("home")

    job = get_object_or_404(JobPosting, pk=pk, recruiter=request.user)

    if request.method == "POST":
        job.delete()
        messages.success(request, "Job deleted.")
        return redirect("recruiter_dashboard")

    return render(request, "jobs/job_confirm_delete.html", {"job": job})


# ── Recruiter: view applicants for a job ──────────────

@login_required
def job_applicants(request, pk):
    if not request.user.is_recruiter():
        return redirect("home")
    job = get_object_or_404(JobPosting, pk=pk, recruiter=request.user)
    apps = Application.objects.filter(job=job).select_related("applicant").order_by("-created_at")
    return render(request, "jobs/job_applicants.html", {"job": job, "applications": apps})


# ── Recruiter: update application status ──────────────

@login_required
def update_application_status(request, app_id):
    if not request.user.is_recruiter():
        return redirect("home")
    app = get_object_or_404(Application, pk=app_id, job__recruiter=request.user)
    if request.method == "POST":
        new_status = request.POST.get("status", "")
        if new_status in dict(Application.Status.choices):
            app.status = new_status
            app.save()
            messages.success(request, f"Status updated to {app.get_status_display()}")
    return redirect("job_applicants", pk=app.job.pk)

# ── Recruiter: candidate search (User Story 11) ───────



@login_required

def recruiter_candidate_search(request):

    if not request.user.is_recruiter():

        return redirect("home")

    skills_q = request.GET.get("skills", "").strip()
    location_q = request.GET.get("location", "").strip()
    projects_q = request.GET.get("projects", "").strip()

    profiles = JobSeekerProfile.objects.select_related("user").filter(
        user__role=CustomUser.Role.JOB_SEEKER
    ).filter(
        Q(is_public=True) | Q(user__applications__job__recruiter=request.user)
    ).distinct()

    if skills_q:
        profiles = profiles.filter(show_skills=True)
        terms = [t.strip() for t in re.split(r"[,\s]+", skills_q) if t.strip()]
        for t in terms:
            profiles = profiles.filter(Q(skills__icontains=t) | Q(user__username__icontains=t))

    if location_q:
        profiles = profiles.filter(show_location=True)
        profiles = profiles.filter(location__icontains=location_q)

    if projects_q:
        profiles = profiles.filter(show_projects=True)
        profiles = profiles.filter(projects__icontains=projects_q)

    return render(request, "jobs/recruiter_candidate_search.html", {
        "profiles": profiles,
        "skills": skills_q,
        "location": location_q,
        "projects": projects_q,
    })

# ── Recruiter: view a candidate's public profile ─────

@login_required
def view_candidate(request, user_id):
    if not request.user.is_recruiter():
        return redirect("home")
    candidate = get_object_or_404(CustomUser, pk=user_id, role=CustomUser.Role.JOB_SEEKER)
    profile = JobSeekerProfile.objects.filter(user=candidate).first()

    if not profile:
        messages.info(request, "This profile is private.")
        return redirect("home")
    has_access = profile.is_public or Application.objects.filter(
        job__recruiter=request.user, applicant=candidate
    ).exists()
    if not has_access:
        messages.info(request, "This profile is private.")
        return redirect("home")

    return render(request, "jobs/view_candidate.html", {
        "candidate": candidate,
        "profile": profile,
    })


# ── Job Seeker Profile ────────────────────────────────

@login_required
def seeker_profile(request):
    if not request.user.is_job_seeker():
        return redirect("home")
    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
    return render(request, "jobs/seeker_profile.html", {"profile": profile})


@login_required
def seeker_profile_edit(request):
    if not request.user.is_job_seeker():
        return redirect("home")
    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = JobSeekerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect("seeker_profile")
    else:
        form = JobSeekerProfileForm(instance=profile)

    return render(request, "jobs/seeker_profile_edit.html", {"form": form})


# ── Admin Views ───────────────────────────────────────

@admin_required
def admin_user_list(request):
    users = CustomUser.objects.all().order_by("username")
    return render(request, "jobs/admin_user_list.html", {"users": users})


@admin_required
def admin_user_update(request, user_id):
    target = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        target.is_active = ("is_active" in request.POST)

        if target.is_recruiter():
            target.is_staff = False
            messages.warning(request, "Recruiters cannot be granted admin rights.")
        else:
            target.is_staff = ("is_staff" in request.POST)

        target.save()
        messages.success(request, f"Updated user: {target.username}")
        return redirect("admin_user_list")

    return render(request, "jobs/admin_user_update.html", {"target_user": target})


@admin_required
def admin_job_list(request):
    jobs = JobPosting.objects.all().order_by("-created_at")
    return render(request, "jobs/admin_job_list.html", {"jobs": jobs})


@admin_required
def admin_job_delete(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)

    if request.method == "POST":
        job.delete()
        messages.success(request, "Job deleted.")
        return redirect("admin_job_list")

    return render(request, "jobs/admin_job_confirm_delete.html", {"job": job})


# ── Recommend jobs ───────────────────────────────────

@login_required
def recommended_jobs(request):
    if not request.user.is_job_seeker():
        return redirect("home")
    profile = JobSeekerProfile.objects.filter(user=request.user).first()
    if not profile or not profile.skills.strip():
        messages.info(request, "Add skills to your profile to get recommendations.")
        return redirect("seeker_profile_edit")
    skills = profile.skills_list()
    q = Q()
    for s in skills:
        q |= Q(skills__icontains=s) | Q(title__icontains=s)
    jobs = JobPosting.objects.filter(is_active=True).filter(q).distinct()[:30]
    return render(request, "jobs/recommended_jobs.html", {"jobs": jobs, "skills": skills})
