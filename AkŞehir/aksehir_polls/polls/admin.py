from django.contrib import admin
from .models import Poll, Choice, Vote

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class PollAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['question_text']}),
        ('Tarih Bilgisi', {'fields': ['pub_date', 'end_date'], 'classes': ['collapse']}),
        ('Durum', {'fields': ['is_active']}),
    ]
    inlines = [ChoiceInline]
    list_display = ('question_text', 'pub_date', 'end_date', 'is_active', 'is_expired')
    list_filter = ['pub_date', 'is_active']
    search_fields = ['question_text']

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('choice_text', 'poll', 'votes_count')
    list_filter = ['poll']
    search_fields = ['choice_text']

class VoteAdmin(admin.ModelAdmin):
    list_display = ('username', 'poll', 'choice', 'created_at')
    list_filter = ['poll', 'created_at']
    search_fields = ['username', 'poll__question_text']

admin.site.register(Poll, PollAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Vote, VoteAdmin)
