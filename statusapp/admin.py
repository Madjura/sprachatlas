from django.contrib import admin

# Register your models here.
from statusapp.models import ProcessStatus

admin.site.register(ProcessStatus)
