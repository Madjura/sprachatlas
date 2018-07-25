"""dragn URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from queryapp.views import query, process, get_provenance, check_all_steps_task_status, suggest_view, frequency_view, \
    query_db
from statusapp.views import status
from uploadapp.views import UploadView

urlpatterns = [
    url(r'^admin/', admin.site.urls, name="admin"),
    url(r'^query/$', query, name="query"),
    url(r'^upload/$', UploadView.as_view(), name="upload"),
    url(r'^process/$', process, name="process"),
    url(r'^provenance/$', get_provenance, name="get_provenance"),
    url(r'^index/$', query, name="index"),
    url(r'^status/$', check_all_steps_task_status, name="all_steps_status"),
    url(r'^suggest/$', suggest_view, name="suggest"),
    url(r'^status-detail/$', status, name="status_detail"),
    url(r'^top-frequencies/$', frequency_view, name="top_frequencies"),
    url(r'^top-frequencies/(?P<pk>[0-9]+)$', frequency_view, name="top_frequencies"),
    url(r'^$', query),
]
