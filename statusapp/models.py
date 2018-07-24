from django.db import models

# Create your models here.
from queryapp.models import TextsAlias


class ProcessStatus(models.Model):
    """Model to keep the ID for Celery tasks, to check how they are progressing."""
    task_id = models.CharField(blank=False, null=False, max_length=100)
    alias = models.ForeignKey(TextsAlias, on_delete=models.CASCADE)
    finished = models.BooleanField(default=False)
