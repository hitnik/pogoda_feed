from django.contrib import admin
from .models import HazardLevels,HazardFeeds

@admin.register(HazardLevels)
class HazardLevelsAdmin(admin.ModelAdmin):
    pass

@admin.register(HazardFeeds)
class HazardFeeds(admin.ModelAdmin):
    pass
