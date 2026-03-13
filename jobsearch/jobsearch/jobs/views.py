from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import Conversation, Message, Application
from .forms import MessageForm, RecruiterProfileForm
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
import datetime
import json
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie



#Neal
from django.utils import timezone
from .models import SavedCandidateSearch, CandidateMatchNotification

#Neal
def _result_user_ids(results):
    ids = []
    for r in results:
        if hasattr(r, "id") and not hasattr(r, "user_id"):
            ids.append(r.id)
        elif hasattr(r, "user_id"):
            ids.append(r.user_id)
    return [i for i in ids if i is not None]

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
from .models import CustomUser, JobPosting, JobSeekerProfile, RecruiterProfile, Application, ProfileReport

# ── Admin guard ────────────────────────────────────────

def is_admin_user(user):
    return user.is_authenticated and user.is_staff

admin_required = user_passes_test(is_admin_user)


# ── Home ───────────────────────────────────────────────

#    This adds match_score to each job card for logged-in seekers.

def home(request):
    jobs = JobPosting.objects.filter(is_active=True)[:6]

    # Annotate match_score for job seekers
    if request.user.is_authenticated and request.user.is_job_seeker():
        profile = JobSeekerProfile.objects.filter(user=request.user).first()
        if profile and profile.skills:
            seeker_skills = {s.strip().lower() for s in profile.skills.split(',') if s.strip()}
            for job in jobs:
                job_skills = {s.strip().lower() for s in job.skills.split(',') if s.strip()}
                if seeker_skills and job_skills:
                    overlap = len(seeker_skills & job_skills)
                    job.match_score = round((overlap / len(job_skills)) * 100) if job_skills else 0
                else:
                    job.match_score = 0

    milestones = None
    if request.user.is_authenticated:
        if request.user.is_job_seeker():
            milestones = get_seeker_milestones(request.user)
        elif request.user.is_recruiter():
            milestones = get_recruiter_milestones(request.user)

    return render(request, "jobs/home.html", {"jobs": jobs, "user_milestones": milestones})

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

# ── REPLACE the existing my_applications view in views.py with this ──────────

@login_required
def my_applications(request):
    if not request.user.is_job_seeker():
        return redirect("home")
    apps = (
        Application.objects
        .filter(applicant=request.user)
        .select_related("job", "applicant__seeker_profile")
        .order_by("-created_at")
    )

    # Status counts for the summary strip
    status_counts = {}
    for a in apps:
        status_counts[a.status] = status_counts.get(a.status, 0) + 1

    return render(request, "jobs/my_applications.html", {
    "applications": apps,
    "status_counts": status_counts,
    "user_milestones": get_seeker_milestones(request.user),
})

# ── Recruiter CRUD ────────────────────────────────────

@login_required
def recruiter_dashboard(request):
    if not request.user.is_recruiter():
        return redirect("home")
    jobs = JobPosting.objects.filter(recruiter=request.user)
    return render(request, "jobs/recruiter_dashboard.html", {
    "jobs": jobs,
    "user_milestones": get_recruiter_milestones(request.user),
})

@login_required
def recruiter_profile(request):
    """View the recruiter's own profile."""
    if not request.user.is_recruiter():
        return redirect("home")
    profile = RecruiterProfile.objects.filter(user=request.user).first()
    return render(request, "jobs/recruiter_profile.html", {"profile": profile})


@login_required
def recruiter_profile_edit(request):
    """Edit the recruiter's profile (company name, website, bio + name)."""
    if not request.user.is_recruiter():
        return redirect("home")

    profile, _ = RecruiterProfile.objects.get_or_create(
        user=request.user,
        defaults={"company_name": ""}
    )

    if request.method == "POST":
        form = RecruiterProfileForm(request.POST, instance=profile)
        if form.is_valid():
            # Update name fields on the user object
            request.user.first_name = request.POST.get("first_name", request.user.first_name).strip()
            request.user.last_name = request.POST.get("last_name", request.user.last_name).strip()
            request.user.save()
            form.save()
            messages.success(request, "Profile updated!")
            return redirect("recruiter_profile")
    else:
        form = RecruiterProfileForm(instance=profile)

    return render(request, "jobs/recruiter_profile_edit.html", {"form": form})


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

    # --- helper to run the exact same filtering logic for any (skills, location, projects) ---
    def filter_profiles(skills_text: str, location_text: str, projects_text: str):
        qs = JobSeekerProfile.objects.filter(is_public=True).select_related("user")

        if skills_text:
            q = Q()
            for term in skills_text.split(","):
                term = term.strip()
                if term:
                    q |= Q(skills__icontains=term)
            qs = qs.filter(q, show_skills=True)

        if location_text:
            qs = qs.filter(location__icontains=location_text, show_location=True)

        if projects_text:
            qs = qs.filter(projects__icontains=projects_text, show_projects=True)

        return qs

    # --- read current search inputs (GET for searching on this page) ---
    skills_q = request.GET.get("skills", "").strip()
    location_q = request.GET.get("location", "").strip()
    projects_q = request.GET.get("projects", "").strip()

    # compute current results shown on page
    profiles = filter_profiles(skills_q, location_q, projects_q)

    # --- Save Search (POST) ---
    # Your template must submit: action=save_search, plus skills/location/projects fields.
    if request.method == "POST" and request.POST.get("action") == "save_search":
        name = (request.POST.get("save_name") or "Saved search").strip()[:80]

        # pull values from POST if present, otherwise fall back to current GET query
        skills_to_save = (request.POST.get("skills") or skills_q).strip()
        location_to_save = (request.POST.get("location") or location_q).strip()
        projects_to_save = (request.POST.get("projects") or projects_q).strip()

        # compute matches for the saved search so we can store "last seen"
        saved_matches = filter_profiles(skills_to_save, location_to_save, projects_to_save)

        SavedCandidateSearch.objects.create(
            recruiter=request.user,
            name=name,
            skills=skills_to_save,
            location=location_to_save,
            projects=projects_to_save,
            last_checked_at=timezone.now(),
            last_seen_candidate_ids=_result_user_ids(saved_matches),
        )
        messages.success(request, f"Saved search '{name}'")

    # --- Check saved searches for new matches + create notifications ---
    saved_searches = SavedCandidateSearch.objects.filter(recruiter=request.user).order_by("-created_at")

    for s in saved_searches:
        current_results = filter_profiles(s.skills or "", s.location or "", s.projects or "")
        current_ids = set(_result_user_ids(current_results))
        old_ids = set(s.last_seen_candidate_ids or [])

        new_ids = current_ids - old_ids
        if new_ids:
            CandidateMatchNotification.objects.create(
                recruiter=request.user,
                saved_search=s,
                message=f"New matches for '{s.name}': {len(new_ids)} candidate(s)"
            )
            s.last_seen_candidate_ids = list(current_ids)
            s.last_checked_at = timezone.now()
            s.save(update_fields=["last_seen_candidate_ids", "last_checked_at"])

    unread_count = CandidateMatchNotification.objects.filter(
        recruiter=request.user,
        is_read=False
    ).count()

    # --- CONTEXT (this is what "add to context" means) ---
    context = {
        "profiles": profiles,
        "skills": skills_q,
        "location": location_q,
        "projects": projects_q,
        "saved_searches": saved_searches,
        "unread_count": unread_count,
    }

    return render(request, "jobs/recruiter_candidate_search.html", context)

# ── Recruiter: applicant pipeline───────────
@login_required
def recruiter_pipeline_data(request):
    if not request.user.is_recruiter():
        return JsonResponse({"error": "forbidden"}, status=403)
    jobs = JobPosting.objects.filter(recruiter=request.user).order_by("-created_at")
    selected_job_id = request.GET.get("job", "").strip()
    job_qs = jobs
    if selected_job_id.isdigit():
        job_qs = job_qs.filter(pk=int(selected_job_id))
    apps = Application.objects.filter(job__in=job_qs).select_related("job", "applicant").order_by("-created_at")

    seeker_profiles = JobSeekerProfile.objects.filter(user__in=[a.applicant for a in apps]).select_related("user")
    seeker_map = {sp.user_id: sp for sp in seeker_profiles}
    columns = {k: [] for k, _ in Application.Status.choices}

    for a in apps:
        sp = seeker_map.get(a.applicant_id)
        headline = ""
        if sp and getattr(sp, "show_headline", False) and getattr(sp, "headline", ""):
            headline = sp.headline

        columns[a.status].append({
            "id": a.id,
            "job_id": a.job_id,
            "job_title": a.job.title,
            "username": a.applicant.username,
            "headline": headline,
            "created_at": a.created_at.strftime("%Y-%m-%d"),
            "view_url": reverse_lazy("view_candidate", kwargs={"user_id": a.applicant_id}),
        })

    return JsonResponse({
        "jobs": [{"id": j.id, "title": j.title} for j in jobs],
        "selected_job": int(selected_job_id) if selected_job_id.isdigit() else None,
        "columns": columns,
        "statuses": [{"key": k, "label": v} for k, v in Application.Status.choices],
    })

@login_required
def update_application_status_ajax(request, app_id):
    if not request.user.is_recruiter():
        return JsonResponse({"error": "forbidden"}, status=403)
    app = get_object_or_404(Application, pk=app_id, job__recruiter=request.user)
    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)
    new_status = request.POST.get("status", "")
    if new_status not in dict(Application.Status.choices):
        return JsonResponse({"error": "invalid_status"}, status=400)
    app.status = new_status
    app.save()

    return JsonResponse({
        "ok": True,
        "app_id": app.id,
        "status": app.status,
        "status_label": app.get_status_display(),
    })

# ── Job Seeker Profile ────────────────────────────────

#    This adds a completion_pct integer (0-100) for the profile completion ring.

@login_required
def seeker_profile(request):
    if not request.user.is_job_seeker():
        return redirect("home")
    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)

    # Compute completion percentage (count filled optional fields too)
    fields_to_check = [
        request.user.first_name, request.user.last_name,
        profile.headline, profile.bio, profile.skills,
        profile.education, profile.work_experience,
        profile.location, profile.links,
    ]
    filled = sum(1 for f in fields_to_check if f and str(f).strip())
    completion_pct = round((filled / len(fields_to_check)) * 100)

    return render(request, "jobs/seeker_profile.html", {
        "profile": profile,
        "completion_pct": completion_pct,
    })

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

@login_required
def inbox(request):
    user = request.user
    if user.is_recruiter():
        convos = Conversation.objects.filter(recruiter=user).order_by("-updated_at")
    elif user.is_job_seeker():
        convos = Conversation.objects.filter(job_seeker=user).order_by("-updated_at")
    else:
        convos = Conversation.objects.none()
    return render(request, "jobs/inbox.html", {"convos": convos})


@login_required
def conversation_detail(request, convo_id):
    convo = get_object_or_404(Conversation, id=convo_id)

    if request.user != convo.recruiter and request.user != convo.job_seeker:
        return HttpResponseForbidden("Not allowed.")

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(
                conversation=convo,
                sender=request.user,
                body=form.cleaned_data["body"]
            )
            convo.save()
            return redirect("conversation_detail", convo_id=convo.id)
    else:
        form = MessageForm()

    return render(
        request,
        "jobs/conversation_detail.html",
        {"convo": convo, "messages": convo.messages.all(), "form": form},
    )


@login_required
def start_conversation(request, application_id):
    # recruiter starts convo from application
    if not request.user.is_recruiter():
        return redirect("home")

    app = get_object_or_404(Application, id=application_id)

    # safety: recruiter must own the job posting
    if app.job.recruiter != request.user:
        return HttpResponseForbidden("Not allowed.")

    convo, _ = Conversation.objects.get_or_create(
        recruiter=request.user,
        job_seeker=app.applicant,   
        application=app            
    )
    return redirect("conversation_detail", convo_id=convo.id)

@login_required
def start_conversation_with_candidate(request, user_id):
    if not request.user.is_recruiter():
        return redirect("home")

    candidate = get_object_or_404(CustomUser, pk=user_id, role=CustomUser.Role.JOB_SEEKER)

    # respect privacy: only allow if public OR already applied to this recruiter
    profile = JobSeekerProfile.objects.filter(user=candidate).first()
    is_applicant = Application.objects.filter(applicant=candidate, job__recruiter=request.user).exists()
    if (not is_applicant) and profile and (not profile.is_public):
        return HttpResponseForbidden("This profile is private.")

    convo, _ = Conversation.objects.get_or_create(
        recruiter=request.user,
        job_seeker=candidate,
        defaults={"application": None},
    )
    return redirect("conversation_detail", convo_id=convo.id)

@login_required
def start_conversation_with_candidate(request, user_id):
    if not request.user.is_recruiter():
        return redirect("home")

    candidate = get_object_or_404(CustomUser, pk=user_id, role=CustomUser.Role.JOB_SEEKER)

    # Privacy rule:
    # allow if candidate is public OR has applied to this recruiter's job
    profile = JobSeekerProfile.objects.filter(user=candidate).first()
    is_applicant = Application.objects.filter(applicant=candidate, job__recruiter=request.user).exists()

    if profile and (not profile.is_public) and (not is_applicant):
        return HttpResponseForbidden("This profile is private.")

    # IMPORTANT: only works if Conversation.application is nullable (null=True, blank=True)
    convo, _ = Conversation.objects.get_or_create(
        recruiter=request.user,
        job_seeker=candidate,
        defaults={"application": None},
    )
    return redirect("conversation_detail", convo_id=convo.id)


# ─────────────────────────────────────────────────────────────────────
# 1. RECRUITER KANBAN PIPELINE VIEW
#    URL: path("recruiter/pipeline/", views.recruiter_pipeline, name="recruiter_pipeline")
# ─────────────────────────────────────────────────────────────────────
@login_required
def recruiter_pipeline(request):
    if not request.user.is_recruiter():
        return redirect("home")
    selected_job = None
    selected_job_id = (request.GET.get("job") or "").strip()

    # All applications for jobs owned by this recruiter
    applications = (
        Application.objects
        .filter(job__recruiter=request.user)
        .select_related("applicant", "applicant__seeker_profile", "job")
        .order_by("-created_at")
    )

    if selected_job_id.isdigit():
        selected_job = JobPosting.objects.filter(
            pk=int(selected_job_id), recruiter=request.user
        ).first()
        if selected_job:
            applications = applications.filter(job=selected_job)

    COLUMNS = [
        ("applied",   "Applied",    "#3b82f6", "📬"),
        ("review",    "In Review",  "#f59e0b", "👀"),
        ("interview", "Interview",  "#8b5cf6", "🎤"),
        ("offer",     "Offer",      "#10b981", "🎉"),
        ("closed",    "Closed",     "#9ca3af", "📁"),
    ]

    return render(request, "jobs/recruiter_pipeline.html", {
        "applications": applications,
        "columns": COLUMNS,
        "selected_job": selected_job,
    })


# ─────────────────────────────────────────────────────────────────────
# 2. AJAX STATUS UPDATE (used by kanban drag-and-drop)
#    URL: path("applications/<int:pk>/status/", views.update_application_status_ajax,
#              name="update_application_status_ajax")
#    Note: you may already have update_application_status — this is the
#          AJAX-only version that returns JSON instead of redirecting.
# ─────────────────────────────────────────────────────────────────────
@login_required
def update_application_status_ajax(request, pk):
    if not request.user.is_recruiter():
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    app = get_object_or_404(Application, pk=pk, job__recruiter=request.user)
    new_status = (request.POST.get("status") or "").strip()
    valid = [s[0] for s in Application.Status.choices]
    if new_status not in valid:
        return JsonResponse({"error": "Invalid status"}, status=400)
    app.status = new_status
    app.save(update_fields=["status"])
    return JsonResponse({"ok": True, "status": new_status, "app_id": app.pk})


# ─────────────────────────────────────────────────────────────────────
# 3. LIVE STATS API (used by home page ticker)
#    URL: path("api/stats/today/", views.stats_today, name="stats_today")
# ─────────────────────────────────────────────────────────────────────
def stats_today(request):
    today = timezone.now().date()
    start = datetime.datetime.combine(today, datetime.time.min, tzinfo=timezone.utc)

    apps_today   = Application.objects.filter(created_at__gte=start).count()
    offers_today = Application.objects.filter(
        created_at__gte=start, status="offer"
    ).count()

    # Top 3 skills from all active job postings
    from collections import Counter
    skill_counter = Counter()
    for job in JobPosting.objects.filter(is_active=True).only("required_skills"):
        if job.required_skills:
            for skill in job.required_skills.split(","):
                s = skill.strip()
                if s:
                    skill_counter[s] += 1
    top_skills = [s for s, _ in skill_counter.most_common(3)]

    return JsonResponse({
        "applications_today": apps_today,
        "offers_today":       offers_today,
        "top_skills":         top_skills,
    })



# ── Helper: compute seeker milestone progress ─────────────────────────
def get_seeker_milestones(user):
    """Returns milestone data dict for a job seeker."""
    profile = getattr(user, 'seeker_profile', None)
    if not profile:
        return None

    apps_count   = Application.objects.filter(applicant=user).count()
    offers_count = Application.objects.filter(applicant=user, status='offer').count()

    goal_apps    = profile.goal_applications or 10
    goal_offers  = profile.goal_offers or 1

    apps_pct     = min(100, round(apps_count  / goal_apps   * 100))
    offers_pct   = min(100, round(offers_count / goal_offers * 100))

    any_unlocked = apps_pct >= 100 or offers_pct >= 100

    return {
        'apps_count':   apps_count,
        'goal_apps':    goal_apps,
        'apps_pct':     apps_pct,
        'offers_count': offers_count,
        'goal_offers':  goal_offers,
        'offers_pct':   offers_pct,
        'unlocked':     any_unlocked,
        'background':   profile.background_image.url if (any_unlocked and profile.background_image) else None,
        'bg_opacity':   profile.background_opacity,
    }


# ── Helper: compute recruiter milestone progress ──────────────────────
def get_recruiter_milestones(user):
    """Returns milestone data dict for a recruiter."""
    profile = getattr(user, 'recruiter_profile', None)
    if not profile:
        return None

    reviewed_count = Application.objects.filter(
        job__recruiter=user
    ).exclude(status='applied').count()

    offers_sent = Application.objects.filter(
        job__recruiter=user, status='offer'
    ).count()

    filled_count = JobPosting.objects.filter(
        recruiter=user, is_active=False
    ).count()

    goal_reviews = profile.goal_reviews or 20
    goal_offers  = profile.goal_offers_sent or 5
    goal_filled  = profile.goal_filled or 3

    reviews_pct = min(100, round(reviewed_count / goal_reviews * 100))
    offers_pct  = min(100, round(offers_sent    / goal_offers  * 100))
    filled_pct  = min(100, round(filled_count   / goal_filled  * 100))

    any_unlocked = reviews_pct >= 100 or offers_pct >= 100 or filled_pct >= 100

    return {
        'reviewed_count': reviewed_count, 'goal_reviews': goal_reviews, 'reviews_pct': reviews_pct,
        'offers_sent':    offers_sent,    'goal_offers':  goal_offers,  'offers_pct':  offers_pct,
        'filled_count':   filled_count,   'goal_filled':  goal_filled,  'filled_pct':  filled_pct,
        'unlocked':       any_unlocked,
        'background':     profile.background_image.url if (any_unlocked and profile.background_image) else None,
        'bg_opacity':     profile.background_opacity,
    }


# ── View: save milestone goals (AJAX POST) ────────────────────────────
# URL: path("milestones/save/", views.save_milestones, name="save_milestones")
@login_required
@ensure_csrf_cookie 
def save_milestones(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if request.user.is_job_seeker():
        profile = request.user.seeker_profile
        profile.goal_applications = int(request.POST.get('goal_applications', 10))
        profile.goal_offers       = int(request.POST.get('goal_offers', 1))
        # Background upload
        if 'background_image' in request.FILES:
            profile.background_image = request.FILES['background_image']
        profile.background_opacity = float(request.POST.get('background_opacity', 0.15))
        profile.save()

    elif request.user.is_recruiter():
        profile = request.user.recruiter_profile
        profile.goal_reviews    = int(request.POST.get('goal_reviews', 20))
        profile.goal_offers_sent = int(request.POST.get('goal_offers_sent', 5))
        profile.goal_filled     = int(request.POST.get('goal_filled', 3))
        if 'background_image' in request.FILES:
            profile.background_image = request.FILES['background_image']
        profile.background_opacity = float(request.POST.get('background_opacity', 0.15))
        profile.save()

    return JsonResponse({'ok': True})


def candidate_cluster_map(request):
    import json
    from .models import JobSeekerProfile

    seekers = JobSeekerProfile.objects.exclude(location__isnull=True).exclude(location__exact="")

    candidates = []
    for s in seekers:
        #print("USER:", s.user.username, "| LOCATION:", s.location)
        candidates.append({
            "name": s.user.username,
            "location": s.location,
        })

    return render(request, "jobs/candidate_cluster_map.html", {
        "candidates_json": json.dumps(candidates)
    })

    # ── Saved Searches list + delete + mark-read ─────────────

#User Story 15

@login_required
def saved_searches_list(request):
    if not request.user.is_recruiter():
        return JsonResponse({"error": "forbidden"}, status=403)

    def filter_profiles(skills_text, location_text, projects_text):
        qs = JobSeekerProfile.objects.filter(is_public=True).select_related("user")
        if skills_text:
            q = Q()
            for term in skills_text.split(","):
                term = term.strip()
                if term:
                    q |= Q(skills__icontains=term)
            qs = qs.filter(q, show_skills=True)
        if location_text:
            qs = qs.filter(location__icontains=location_text, show_location=True)
        if projects_text:
            qs = qs.filter(projects__icontains=projects_text, show_projects=True)
        return qs

    searches = SavedCandidateSearch.objects.filter(
        recruiter=request.user
    ).order_by("-created_at")

    data = []
    for s in searches:
        unread = CandidateMatchNotification.objects.filter(
            saved_search=s, is_read=False
        ).count()
        current_count = filter_profiles(
            s.skills or "", s.location or "", s.projects or ""
        ).count()
        data.append({
            "id": s.id,
            "name": s.name,
            "skills": s.skills,
            "location": s.location,
            "projects": s.projects,
            "created_at": s.created_at.strftime("%b %d, %Y"),
            "unread_notifications": unread,
            "current_match_count": current_count,
        })

    return JsonResponse({"searches": data})


@login_required
def delete_saved_search(request, search_id):
    if not request.user.is_recruiter():
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    s = get_object_or_404(SavedCandidateSearch, pk=search_id, recruiter=request.user)
    s.delete()
    return JsonResponse({"ok": True})


@login_required
def mark_search_notifications_read(request, search_id):
    if not request.user.is_recruiter():
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    CandidateMatchNotification.objects.filter(
        recruiter=request.user,
        saved_search_id=search_id,
        is_read=False
    ).update(is_read=True)
    return JsonResponse({"ok": True})
