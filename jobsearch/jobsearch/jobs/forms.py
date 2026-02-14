from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, JobSeekerProfile, RecruiterProfile


class JobSeekerRegistrationForm(UserCreationForm):
    headline = forms.CharField(max_length=200, required=False)
    skills = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.JOB_SEEKER
        if commit:
            user.save()
            JobSeekerProfile.objects.create(
                user=user,
                headline=self.cleaned_data.get("headline", ""),
                skills=self.cleaned_data.get("skills", ""),
            )
        return user


class RecruiterRegistrationForm(UserCreationForm):
    company_name = forms.CharField(max_length=200)
    company_website = forms.URLField(required=False)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.RECRUITER
        if commit:
            user.save()
            RecruiterProfile.objects.create(
                user=user,
                company_name=self.cleaned_data["company_name"],
                company_website=self.cleaned_data.get("company_website", ""),
            )
        return user
    

from .models import CustomUser, JobSeekerProfile, RecruiterProfile, JobPosting


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            "title", "company", "description", "skills", "location",
            "latitude", "longitude", "job_type", "experience_level",
            "salary_min", "salary_max", "visa_sponsorship",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "skills": forms.TextInput(attrs={"placeholder": "Python, Django, SQL"}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            "headline", "skills", "education", "work_experience",
            "links", "location", "is_public",
        ]
        widgets = {
            "headline": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Aspiring Software Engineer"}),
            "skills": forms.TextInput(attrs={"class": "form-control", "placeholder": "Python, Django, SQL, etc."}),
            "education": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "BS Computer Science, Georgia Tech, 2025"}),
            "work_experience": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Software Intern at Google, Summer 2024..."}),
            "links": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "GitHub, LinkedIn, portfolio URLs"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Atlanta, GA"}),
        }