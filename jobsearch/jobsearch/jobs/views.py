# jobs/views.py — replace entire file

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import JobSeekerRegistrationForm, RecruiterRegistrationForm, JobPostingForm
from .models import CustomUser, JobPosting
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

def is_admin_user(user):
    # Option 1 (recommended): use Django's built-in staff flag
    return user.is_authenticated and user.is_staff

admin_required = user_passes_test(is_admin_user)


def home(request):
    jobs = JobPosting.objects.filter(is_active=True)[:6]
    return render(request, "jobs/home.html", {"jobs": jobs})


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
    return render(request, "jobs/job_detail.html", {"job": job})


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
    job = get_object_or_404(JobPosting, pk=pk, recruiter=request.user)
    if request.method == "POST":
        job.delete()
        return redirect("recruiter_dashboard")
    return render(request, "jobs/job_confirm_delete.html", {"job": job})


#ADMIN VIEWS

@admin_required
def admin_user_list(request):
    users = CustomUser.objects.all().order_by("username")
    return render(request, "jobs/admin_user_list.html", {"users": users})


@admin_required
def admin_user_update(request, user_id):
    target = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        target.is_active = ("is_active" in request.POST)

        # Recruiters are NEVER allowed to become admin
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
