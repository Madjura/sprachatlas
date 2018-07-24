from django.shortcuts import render
from celery.result import AsyncResult

# Create your views here.
from queryapp.tasks import all_steps_task
from statusapp.models import ProcessStatus


def status(request):
    context = {"status": []}
    unfinished = ProcessStatus.objects.filter(finished=False)
    status_list = []
    for s in unfinished:
        result = AsyncResult(id=s.task_id, app=all_steps_task)
        status_list.append([s, result.state])
    context["status"] = status_list
    return render(request, "statusapp/status.html", context)