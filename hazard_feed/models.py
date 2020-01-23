from django.db import models
from django.core.validators import MaxValueValidator
from django.utils.translation import gettext as _

# Create your models here.

class HazardLevels(models.Model):
    title = models.CharField(max_length=32)
    danger_level = models.IntegerField(validators=[MaxValueValidator(10)])
    description = models.TextField()

    class Meta:
        verbose_name = _('Hazard Level')
        verbose_name_plural = _('Hazard Levels')

class HazardFeeds(models.Model):
    id = models.BigIntegerField(primary_key=True)
    date = models.DateTimeField()
    title = models.CharField(max_length=128)
    link = models.URLField()
    summary = models.TextField()
    date_modified = models.DateTimeField()
    hazard_level = models.ForeignKey(HazardLevels, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Hazard Feed')
        verbose_name_plural = _('Hazard Feeds')
