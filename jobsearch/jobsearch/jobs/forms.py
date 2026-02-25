from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, JobSeekerProfile, RecruiterProfile, JobPosting, Application, ProfileReport

FC = {"class": "form-control"}
FS = {"class": "form-select"}


class JobSeekerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={**FC, "placeholder": "First name"}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={**FC, "placeholder": "Last name"}))

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.JOB_SEEKER
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            JobSeekerProfile.objects.create(user=user)
        return user


class RecruiterRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={**FC, "placeholder": "First name"}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={**FC, "placeholder": "Last name"}))
    company_name = forms.CharField(max_length=200)
    company_website = forms.URLField(required=False)

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.RECRUITER
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            RecruiterProfile.objects.create(
                user=user,
                company_name=self.cleaned_data["company_name"],
                company_website=self.cleaned_data.get("company_website", ""),
            )
        return user


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            "title", "company", "description", "skills", "location",
            "latitude", "longitude", "job_type", "experience_level",
            "salary_min", "salary_max", "visa_sponsorship",
        ]
        widgets = {
            "title": forms.TextInput(attrs={**FC, "placeholder": "e.g. Software Engineer Intern"}),
            "company": forms.TextInput(attrs={**FC, "placeholder": "e.g. Google"}),
            "description": forms.Textarea(attrs={**FC, "rows": 5, "placeholder": "Describe the role…"}),
            "skills": forms.TextInput(attrs={**FC, "placeholder": "Python, Django, SQL"}),
            "location": forms.TextInput(attrs={**FC, "placeholder": "e.g. Atlanta, GA"}),
            "job_type": forms.Select(attrs=FS),
            "experience_level": forms.Select(attrs=FS),
            "salary_min": forms.NumberInput(attrs={**FC, "placeholder": "e.g. 60000"}),
            "salary_max": forms.NumberInput(attrs={**FC, "placeholder": "e.g. 90000"}),
            "visa_sponsorship": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }


class SeekerIdentityForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={**FC, "placeholder": "First name"}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={**FC, "placeholder": "Last name"}))


class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            "profile_picture", "headline", "bio", "location", "phone", "website",
            "skills", "education", "work_experience", "projects",
            "certifications", "languages", "links",
            "featured_label", "featured_url", "featured_video_url",
            "desired_job_title", "desired_salary_min",
            "commute_distance", "distance_unit",
            "open_to_remote", "open_to_relocation", "visa_required",
        ]
        widgets = {
            "profile_picture": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "headline": forms.TextInput(attrs={**FC, "placeholder": "e.g. Aspiring Software Engineer"}),
            "bio": forms.Textarea(attrs={**FC, "rows": 3, "placeholder": "A short summary about yourself…"}),
            "location": forms.TextInput(attrs={**FC, "placeholder": "Atlanta, GA"}),
            "phone": forms.TextInput(attrs={**FC, "placeholder": "+1 (555) 123-4567"}),
            "website": forms.URLInput(attrs={**FC, "placeholder": "https://yoursite.com"}),
            "skills": forms.TextInput(attrs={**FC, "placeholder": "Python, Django, SQL, etc."}),
            "education": forms.Textarea(attrs={**FC, "rows": 3, "placeholder": "BS Computer Science, Georgia Tech, 2025"}),
            "work_experience": forms.Textarea(attrs={**FC, "rows": 4, "placeholder": "Software Intern — Google — Summer 2024"}),
            "projects": forms.Textarea(attrs={**FC, "rows": 3, "placeholder": "Neutrino Event Classifier — ML pipeline for telescope data"}),
            "certifications": forms.Textarea(attrs={**FC, "rows": 2, "placeholder": "AWS Cloud Practitioner, 2024"}),
            "languages": forms.TextInput(attrs={**FC, "placeholder": "English (Native), Spanish (Conversational)"}),
            "links": forms.Textarea(attrs={**FC, "rows": 2, "placeholder": "https://github.com/you\nhttps://linkedin.com/in/you"}),
            "featured_label": forms.TextInput(attrs={**FC, "placeholder": "e.g. My Portfolio, Intro Video, Senior Project"}),
            "featured_url": forms.URLInput(attrs={**FC, "placeholder": "https://myportfolio.com"}),
            "featured_video_url": forms.URLInput(attrs={**FC, "placeholder": "https://youtube.com/watch?v=..."}),
            "desired_job_title": forms.TextInput(attrs={**FC, "placeholder": "e.g. Software Engineer"}),
            "desired_salary_min": forms.NumberInput(attrs={**FC, "placeholder": "e.g. 70000"}),
            "commute_distance": forms.NumberInput(attrs={**FC, "placeholder": "e.g. 25"}),
            "distance_unit": forms.Select(attrs=FS),
        }


class SeekerPrivacyForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            "is_public", "show_photo", "show_headline", "show_bio",
            "show_skills", "show_education", "show_experience",
            "show_projects", "show_certifications", "show_languages",
            "show_links", "show_location", "show_phone", "show_email",
            "show_featured",
        ]


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["note"]
        widgets = {
            "note": forms.Textarea(attrs={
                **FC, "rows": 4,
                "placeholder": "Write a tailored note to stand out (optional)",
            })
        }


class ProfileReportForm(forms.ModelForm):
    class Meta:
        model = ProfileReport
        fields = ["reason", "details"]
        widgets = {
            "reason": forms.Select(attrs=FS),
            "details": forms.Textarea(attrs={
                **FC, "rows": 3,
                "placeholder": "Any additional context (optional)",
            }),
        }