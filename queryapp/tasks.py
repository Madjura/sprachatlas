from celery import shared_task

from allsteps.allsteps import all_steps


@shared_task(bind=True)
def all_steps_task(self, texts, language, alias):
    all_steps(texts, language=language, alias=alias, task=all_steps_task, task_id=self.request.id)
