from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from .forms import (
    JobSeekerRegistrationForm,
    RecruiterRegistrationForm,
    JobPostingForm,
    JobSeekerProfileForm,
    SeekerIdentityForm,
    SeekerPrivacyForm,
    ApplicationForm,
    ProfileReportForm,
)
from .models import CustomUser, JobPosting, JobSeekerProfile, Application, ProfileReport


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
        return reverse_lazy("home")


# ── Auth ──────────────────────────────────────────────

def register_seeker(request):
    if request.method == "POST":
        form = JobSeekerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Complete your profile to start applying.")
            return redirect("seeker_profile_edit")
    else:
        form = JobSeekerRegistrationForm()
    return render(request, "jobs/register.html", {"form": form, "role": "Job Seeker"})


def register_recruiter(request):
    if request.method == "POST":
        form = RecruiterRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("recruiter_dashboard")
    else:
        form = RecruiterRegistrationForm()
    return render(request, "jobs/register.html", {"form": form, "role": "Recruiter"})


def job_map(request):
    jobs = JobPosting.objects.filter(
        is_active=True, latitude__isnull=False, longitude__isnull=False
    )
    commute_distance = 10
    distance_unit = "mi"
    if request.user.is_authenticated and request.user.is_job_seeker():
        profile = JobSeekerProfile.objects.filter(user=request.user).first()
        if profile:
            if profile.commute_distance:
                commute_distance = profile.commute_distance
            distance_unit = profile.distance_unit or "mi"
    return render(request, "jobs/job_map.html", {
        "jobs": jobs,
        "commute_distance": commute_distance,
        "distance_unit": distance_unit,
    })


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
        jobs = jobs.filter(Q(title__icontains=q) | Q(skills__icontains=q) | Q(company__icontains=q))
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

    return render(request, "jobs/job_list.html", {
        "jobs": jobs, "q": q, "location": location, "job_type": job_type,
        "experience": experience, "visa": visa, "salary_min": salary_min,
        "job_type_choices": JobPosting.JobType.choices,
        "experience_choices": JobPosting.ExperienceLevel.choices,
    })


def job_detail(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    already_applied = False
    profile_complete = True
    if request.user.is_authenticated and request.user.is_job_seeker():
        already_applied = Application.objects.filter(job=job, applicant=request.user).exists()
        profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
        profile_complete = profile.is_complete()
    return render(request, "jobs/job_detail.html", {
        "job": job, "already_applied": already_applied, "profile_complete": profile_complete,
    })


# ── Apply to job ───────────────────────────────────────

@login_required
def apply_to_job(request, pk):
    if not request.user.is_job_seeker():
        return redirect("home")
    job = get_object_or_404(JobPosting, pk=pk)

    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
    if not profile.is_complete():
        missing = ", ".join(profile.completion_missing())
        messages.warning(request, f"Complete your profile before applying. Missing: {missing}")
        return redirect("seeker_profile_edit")

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


# ── My Applications ───────────────────────────────────

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
    jobs = JobPosting.objects.filter(recruiter=request.user)
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
            return redirect("recruiter_dashboard")
    else:
        form = JobPostingForm()
    return render(request, "jobs/job_form.html", {"form": form, "editing": False})


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
    return render(request, "jobs/job_form.html", {"form": form, "editing": True})


@login_required
def job_delete(request, pk):
    if not request.user.is_recruiter():
        return redirect("home")
    job = get_object_or_404(JobPosting, pk=pk, recruiter=request.user)
    if request.method == "POST":
        job.delete()
        return redirect("recruiter_dashboard")
    return render(request, "jobs/job_confirm_delete.html", {"job": job})


# ── Recruiter: applicants + status ────────────────────

@login_required
def job_applicants(request, pk):
    if not request.user.is_recruiter():
        return redirect("home")
    job = get_object_or_404(JobPosting, pk=pk, recruiter=request.user)
    apps = Application.objects.filter(job=job).select_related("applicant").order_by("-created_at")
    return render(request, "jobs/job_applicants.html", {"job": job, "applications": apps})


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


# ── View candidate (full for applicants, filtered otherwise) ──

@login_required
def view_candidate(request, user_id):
    if not request.user.is_recruiter():
        return redirect("home")
    candidate = get_object_or_404(CustomUser, pk=user_id, role=CustomUser.Role.JOB_SEEKER)
    profile = JobSeekerProfile.objects.filter(user=candidate).first()
    if not profile:
        messages.info(request, "This candidate has no profile.")
        return redirect("home")

    is_applicant = Application.objects.filter(
        applicant=candidate, job__recruiter=request.user
    ).exists()

    if not is_applicant and not profile.is_public:
        messages.info(request, "This profile is private.")
        return redirect("home")

    show_featured = bool(is_applicant or getattr(profile, "show_featured", False))

    return render(request, "jobs/view_candidate.html", {
        "candidate": candidate,
        "profile": profile,
        "is_applicant": is_applicant,
        "show_featured": show_featured,
    })


# ── Report a profile ─────────────────────────────────

@login_required
def report_profile(request, user_id):
    candidate = get_object_or_404(CustomUser, pk=user_id, role=CustomUser.Role.JOB_SEEKER)
    profile = get_object_or_404(JobSeekerProfile, user=candidate)

    # Prevent self-reporting
    if request.user == candidate:
        return redirect("home")

    # Prevent duplicate reports
    if ProfileReport.objects.filter(profile=profile, reported_by=request.user).exists():
        messages.info(request, "You have already reported this profile.")
        return redirect("view_candidate", user_id=user_id)

    if request.method == "POST":
        form = ProfileReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.profile = profile
            report.reported_by = request.user
            report.save()
            messages.success(request, "Report submitted. An admin will review it.")
            return redirect("view_candidate", user_id=user_id)
    else:
        form = ProfileReportForm()

    return render(request, "jobs/report_profile.html", {
        "candidate": candidate, "form": form,
    })


# ── Recruiter: candidate search ──────────────────────

@login_required
def recruiter_candidate_search(request):
    if not request.user.is_recruiter():
        return redirect("home")

    skills_q = request.GET.get("skills", "").strip()
    location_q = request.GET.get("location", "").strip()
    projects_q = request.GET.get("projects", "").strip()

    profiles = JobSeekerProfile.objects.filter(is_public=True).select_related("user")

    if skills_q:
        q = Q()
        for term in skills_q.split(","):
            term = term.strip()
            if term:
                q |= Q(skills__icontains=term)
        profiles = profiles.filter(q, show_skills=True)
    if location_q:
        profiles = profiles.filter(location__icontains=location_q, show_location=True)
    if projects_q:
        profiles = profiles.filter(projects__icontains=projects_q, show_projects=True)

    return render(request, "jobs/recruiter_candidate_search.html", {
        "profiles": profiles, "skills": skills_q, "location": location_q, "projects": projects_q,
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
        identity_form = SeekerIdentityForm(request.POST)
        profile_form = JobSeekerProfileForm(request.POST, request.FILES, instance=profile)
        privacy_form = SeekerPrivacyForm(request.POST, instance=profile)

        if identity_form.is_valid() and profile_form.is_valid() and privacy_form.is_valid():
            request.user.first_name = identity_form.cleaned_data["first_name"]
            request.user.last_name = identity_form.cleaned_data["last_name"]
            request.user.save()

            p = profile_form.save(commit=False)
            for field in SeekerPrivacyForm.Meta.fields:
                setattr(p, field, privacy_form.cleaned_data[field])
            p.save()

            messages.success(request, "Profile updated!")
            return redirect("seeker_profile")
    else:
        identity_form = SeekerIdentityForm(initial={
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
        })
        profile_form = JobSeekerProfileForm(instance=profile)
        privacy_form = SeekerPrivacyForm(instance=profile)

    return render(request, "jobs/seeker_profile_edit.html", {
        "identity_form": identity_form,
        "profile_form": profile_form,
        "privacy_form": privacy_form,
        "profile": profile,
    })


# ── Delete Account ────────────────────────────────────

@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect("home")
    return render(request, "jobs/delete_account.html")


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
    jobs = JobPosting.objects.all().order_by("-id")
    return render(request, "jobs/admin_job_list.html", {"jobs": jobs})


@admin_required
def admin_job_delete(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    if request.method == "POST":
        job.delete()
        messages.success(request, "Job post removed.")
        return redirect("admin_job_list")
    return render(request, "jobs/admin_job_confirm_delete.html", {"job": job})


@admin_required
def admin_report_list(request):
    reports = ProfileReport.objects.select_related("profile__user", "reported_by").all()
    return render(request, "jobs/admin_report_list.html", {"reports": reports})


@admin_required
def admin_report_resolve(request, pk):
    report = get_object_or_404(ProfileReport, pk=pk)
    if request.method == "POST":
        report.reviewed = True
        report.save()
        messages.success(request, "Report marked as reviewed.")
    return redirect("admin_report_list")


# ── Recommend jobs ────────────────────────────────────

@login_required
def recommended_jobs(request):
    if not request.user.is_job_seeker():
        return redirect("home")
    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)
    skills_list = [s.strip() for s in (profile.skills or "").split(",") if s.strip()]

    jobs = JobPosting.objects.filter(is_active=True)
    recommended = []
    if skills_list:
        for job in jobs:
            text = f"{job.title} {job.description} {getattr(job, 'skills', '')} {job.company}".lower()
            if any(skill.lower() in text for skill in skills_list):
                recommended.append(job)

    return render(request, "jobs/recommended_jobs.html", {
        "jobs": recommended, "skills_list": skills_list,

    })
    
# ── Recommend candidates ─────────────────────────────
@login_required
def recommended_candidates(request):
    if not request.user.is_recruiter():
        return redirect("home")

    postings = JobPosting.objects.filter(recruiter=request.user, is_active=True)
    selected_job = None
    job_id = request.GET.get("job")
    if job_id:
        try:
            selected_job = postings.get(pk=int(job_id))
        except (ValueError, JobPosting.DoesNotExist):
            selected_job = None
    if selected_job is None:
        selected_job = postings.first()

    job_skills = []
    if selected_job:
        job_skills = [s.strip() for s in (selected_job.skills or "").split(",") if s.strip()]

    seeker_profiles = JobSeekerProfile.objects.select_related("user").filter(
        is_public=True,
        user__role=CustomUser.Role.JOB_SEEKER,
    )
    
    candidates = []
    if job_skills:
        job_skill_set = {s.lower() for s in job_skills}
        for p in seeker_profiles:
            if not p.show_skills:
                continue
            cand_skills = [s.strip() for s in (p.skills or "").split(",") if s.strip()]
            overlap = sorted({s for s in cand_skills if s.lower() in job_skill_set}, key=lambda x: x.lower())
            if overlap:
                p.overlap_skills = overlap
                p.overlap_count = len(overlap)
                candidates.append(p)

        candidates.sort(key=lambda p: (-getattr(p, "overlap_count", 0), p.user.username.lower()))

    return render(request, "jobs/recommended_candidates.html", {
        "postings": postings,
        "selected_job": selected_job,
        "job_skills": job_skills,
        "candidates": candidates,
    })

