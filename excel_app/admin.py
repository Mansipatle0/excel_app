from django.contrib import admin
from .models import ExcelUpload, Checklist

@admin.register(ExcelUpload)
class ExcelUploadAdmin(admin.ModelAdmin):
    list_display = ('excel_name','source','count','date_added')
    search_fields = ('excel_name','source')

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('excel','status','scheduled_at','created_at')
    list_filter = ('status',)
