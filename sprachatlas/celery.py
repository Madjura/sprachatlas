import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sprachatlas.settings')

app = Celery('dragn', backend="amqp")
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# celery -A sprachatlas worker -l info -P eventlet