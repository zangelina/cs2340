from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, JobSeekerProfile, RecruiterProfile, JobPosting, Application


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


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            "title", "company", "description", "skills", "location",
            "latitude", "longitude", "job_type", "experience_level",
            "salary_min", "salary_max", "visa_sponsorship",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Software Engineer Intern"
            }),
            "company": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Google"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Describe the role, responsibilities, and requirements..."
            }),
            "skills": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Python, Django, SQL"
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Atlanta, GA"
            }),
            "job_type": forms.Select(attrs={"class": "form-select"}),
            "experience_level": forms.Select(attrs={"class": "form-select"}),
            "salary_min": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 60000"
            }),
            "salary_max": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 90000"
            }),
            "visa_sponsorship": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }


class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = [
            "headline", "skills", "education", "work_experience",
            "links", "projects", "location",
            "show_headline", "show_skills", "show_education",
            "show_experience", "show_links", "show_projects", "show_location",
            "is_public",
        ]
        widgets = {
            "headline": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Aspiring Software Engineer"
            }),
            "skills": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Python, Django, SQL, etc."
            }),
            "education": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "BS Computer Science, Georgia Tech, 2025"
            }),
            "work_experience": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Software Intern at Google, Summer 2024..."
            }),
            "links": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "GitHub, LinkedIn, portfolio URLs"
            }),
            "projects": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Project highlights (e.g. Built a Django job board, ML classifier, etc.)"
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Atlanta, GA"
            }),
        }
        labels = {
            "show_headline": "Show headline to recruiters",
            "show_skills": "Show skills to recruiters",
            "show_education": "Show education to recruiters",
            "show_experience": "Show work experience to recruiters",
            "show_links": "Show links to recruiters",
            "show_projects": "Show projects to recruiters",
            "show_location": "Show location to recruiters",
            "is_public": "Make entire profile discoverable by recruiters",
        }


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["note"]
        widgets = {
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Write a tailored note to stand out (optional)",
            })
        }
