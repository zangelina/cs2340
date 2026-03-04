from django.contrib import admin
from .models import CustomUser, JobPosting

#Neal
from .models import SavedCandidateSearch, CandidateMatchNotification


admin.site.register(CustomUser)
admin.site.register(JobPosting)

#Neal
admin.site.register(SavedCandidateSearch)
admin.site.register(CandidateMatchNotification)