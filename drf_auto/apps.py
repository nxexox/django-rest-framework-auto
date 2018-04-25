from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DRFAutoConfig(AppConfig):
    name = "drf_auto"
    verbose_name = _("DRFAuto")
