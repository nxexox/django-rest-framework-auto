from django.conf import settings


# Описание кода и ошибок.
CODES = {'common': {}, 'specific': {}}


class DRFSettings(object):
    """
    Настройки только для документации.

    """
    def __init__(self):
        self.HIDE_DOCS = self.get_setting('HIDE_DOCS') or False
        # Используется для поиска атрибута, который отвечает за документацию.
        self.SERIALIZERS_ATTR_NAME = self.get_setting('SERIALIZERS_ATTR_NAME', 'docs_serializer_classes')
        # Используется для исключения филдов из доки.
        self.EXCLUDE_FIELDS_ATTR_NAME = self.get_setting('EXCLUDE_FIELDS_ATTR_NAME', 'docs_exclude_fields')
        # НУЖНО ДЛЯ ТОГО, ЧТО БЫ описать SerialiazerMethodField у сериалайзеров.
        # Прописывать в serializer.Meta классе. Даже если класс не ModelSerializer.
        self.SERIALIZER_DOC_ATTR = self.get_setting('SERIALIZER_DOC_ATTR', 'doc_method_fields_classes')
        self.CODES = self.get_setting('SERIALIZER_DOC_CODES', CODES)

    def get_setting(self, name, default=None):
        try:
            return settings.REST_FRAMEWORK_AUTO[name]
        except:
            return default

    def get_code(self, code):
        """
        Возвращает объект кода.

        :param str code: Номер кода, который необходимо вернуть.

        :return: Сообщение об ошибке. соотвествующее этому коду.
        :rtype: str

        """
        return self.CODES.get('specific', {}).get(str(code))


DocsSettings = DRFSettings()
