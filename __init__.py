import os

from .celery import app as celery_app

__all__ = ['celery_app']


def setup():
    """
    This method must be called every time anything related to Django is imported in modules
    that are not necessarily used only when Django is running.
    :return:
    """
    _module = os.path.split(os.path.dirname(__file__))[-1]
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{}.settings".format(_module))
    import django
    django.setup()
