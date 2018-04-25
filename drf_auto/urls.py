"""
Урлы для автодоки.

"""

from django.conf.urls import url

from .views import DRFDocsView


urlpatterns = [
    url(r'^$', DRFDocsView.as_view(), name='docs'),
]
