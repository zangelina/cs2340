from django.contrib import admin
from django.http import HttpResponse 
import csv
from .models import CustomUser, JobPosting

#Neal
from .models import SavedCandidateSearch, CandidateMatchNotification
def export_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=export.csv'
    writer = csv.writer(response)
    fields = [field.name for field in queryset.model._meta.fields]
    writer.writerow(fields)
    for obj in queryset:
        row = []
        for field in fields:
            row.append(getattr(obj, field))
        writer.writerow(row)
    return response
export_csv.short_description = "Download CSV for selected rows"
class CustomUserAdmin(admin.ModelAdmin):
    actions = [export_csv]
class JobPostingAdmin(admin.ModelAdmin):
    actions = [export_csv]
class SavedCandidateSearchAdmin(admin.ModelAdmin):
    actions = [export_csv]
class CandidateMatchNotificationAdmin(admin.ModelAdmin):
    actions = [export_csv]
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(JobPosting, JobPostingAdmin)
#Neal
admin.site.register(SavedCandidateSearch, SavedCandidateSearchAdmin)
admin.site.register(CandidateMatchNotification, CandidateMatchNotificationAdmin)
