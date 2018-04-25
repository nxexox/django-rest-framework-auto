"""
Настройки всего приложения.

"""
from django.conf import settings

from .autodocs.settings import DocsSettings


class DRFSettings(object):
    """
    Настройки для всего приложения.

    """
    def __init__(self):
        self.DOCS = DocsSettings
        # Название филда, для поиска словаря сериалайзеров для ответа.
        self.SERIALIZERS_RESPONSE_FIELD = self.get_setting('SERIALIZERS_RESPONSE_FIELD', 'serializer_classes')
        # Название филда, для поиска словаря сериалайзеров для обработки запроса.
        self.SERIALIZERS_REQUEST_FIELD = self.get_setting('SERIALIZERS_REQUEST_FIELD', 'serializer_classes')
        # Эти ключи используются для поиска внутри сериалайзеров. IN - обработка водящих данных.
        self.SERIALIZERS_REQUEST_KEY = self.get_setting('SERIALIZERS_REQUEST_KEY', 'in')
        # out - обработка ответа сервера.
        self.SERIALIZERS_RESPONSE_KEY = self.get_setting('SERIALIZERS_RESPONSE_KEY', 'out')

    def get_setting(self, name, default=None):
        try:
            return settings.REST_FRAMEWORK_AUTO[name]
        except:
            return default


DefaultSettings = DRFSettings()
