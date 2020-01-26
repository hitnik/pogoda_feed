from django.contrib import admin
from .models import HazardLevels,HazardFeeds, EmailRecipients

@admin.register(HazardLevels)
class HazardLevelsAdmin(admin.ModelAdmin):
    pass

@admin.register(HazardFeeds)
class HazardFeedsAdmin(admin.ModelAdmin):
    pass

@admin.register(EmailRecipients)
class EmailRecipientsAdmin(admin.ModelAdmin):
    pass