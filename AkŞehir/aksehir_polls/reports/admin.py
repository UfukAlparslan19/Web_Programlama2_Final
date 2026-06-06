from django.contrib import admin
from .models import Report

class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'ai_risk_level', 'status', 'created_at')
    list_filter = ('status', 'category', 'ai_risk_level', 'created_at')
    search_fields = ('user__username', 'category', 'address', 'ai_description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

admin.site.register(Report, ReportAdmin)
