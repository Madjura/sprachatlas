import os

from .celery import app as celery_app

__all__ = ['celery_app']


def setup():
    _module = os.path.split(os.path.dirname(__file__))[-1]
    os.environ.setdefault("SPRACHATLAS_SETTINGS_MODULE", "{}.settings".format(_module))
    import django
    django.setup()
