"""
Настройки всего приложения.

"""
import logging
from importlib import import_module

import six

from django.conf import settings


logger = logging.getLogger(__name__)

# Описание кода и ошибок.
CODES = {'common': {}, 'specific': {}}

# Дефолтные настройки.
__DEFAULTS = {
    'DOCS': {
        'HIDE_DOCS': False,
        'SERIALIZERS_ATTR_NAME': 'docs_serializer_classes',
        'EXCLUDE_FIELDS_ATTR_NAME': 'docs_exclude_fields',
        'SERIALIZER_DOC_ATTR': 'doc_method_fields_classes',
        'PARSER_CLASS': 'drf_auto.autodocs.parsers.DefaultParser',
    },
    'AUTO_REST': {
        'EXCEPTIONS': {
            'PROCESS_EXCEPT': True,  # Нужно ли обработать ошибки?
            'PROCESS_EXCEPT_HANDLER': None,  # Свой обработчик ошибок.
            # Список исключений, которые обрабатываем.
            'EXCEPTION_LIST': ['rest_framework.serializers.ValidationError'],
            'CODE_EXCEPTION_LIST': 400,  # Код ответа апи при обработке исключний.
            'STATUS_EXCEPTION_LIST': 400,  # Код ответа сервера при обработке исключений.
        },
    },
    'CODES': CODES,
    'SERIALIZERS_RESPONSE_FIELD': 'serializer_classes',
    'SERIALIZERS_REQUEST_FIELD': 'serializer_classes',
    'SERIALIZERS_REQUEST_KEY': 'in',
    'SERIALIZERS_RESPONSE_KEY': 'out'
}

# Настройки, которые нужно импортировать как классы/функции. Вложенность через .
__IMPORTS = {
    'DOCS.PARSER_CLASS',
    'AUTO_REST.EXCEPTIONS.EXCEPTION_LIST', 'AUTO_REST.EXCEPTIONS.PROCESS_EXCEPT_HANDLER'
}
# Настройки которые не нужно создавать как подкласс настроек, а брать прямо как указано. Вложенность через .
__NOT_CREATE_SETTINGS = {
    'CODES'
}


class DRFSettings(object):
    """
    Настройки для всего приложения.

    """
    def __init__(self, defaults=None, imports=None, user_settings=None, not_create=None, is_root=True):
        """
        Создаем класс настроек.

        :param dict defaults: Дефолтные настройки для текущего приложения.
        :param iter imports: Множество настроек, которое нужно импортировать для текущего приложения.
        :param dict user_settings: Пользовательские настройки для текущего приложения.
        :param iter not_create: Настройки, которые не нужно превращать в подкласс настроек.
        :param bool is_root: Флаг, указывающий это главный объект настроек или нет.
                             Используется для поиска пользовательяких настроек.

        """
        self.__defaults = defaults or globals().get('__DEFAULTS')
        self.__imports = imports or globals().get('__IMPORTS')
        self.__not_create = not_create or globals().get('__NOT_CREATE_SETTINGS')

        # Ищем пользовательские настройки.
        _u_s = user_settings or {}
        if not _u_s and is_root:
            _u_s = getattr(settings, 'REST_FRAMEWORK_AUTO', {})
        self.__user_settings = _u_s

    def __getattr__(self, attr):
        """
        Подменяем пути до классов самими классами.
        Поиск делится 5 этапов:
            1. Смотрим есть ли такой атриюут в дефолтных настройках.
            2. Смотрим вложеный ли это атрибут. Если вложенный, тогда смотрим надо ли его превращать в класс настроек.
               Если надо, создаем класс настроек с настройками всей вложенности, ставим его текущему классу,
               и возвращаем его. Далее алгоритм поиска идет уже в этот класс и все по новой.
               Пока не доберется до объекта без вложенности.
            3. Когда добраились до простого объекта, смотрим, установил ли пользователь свое значение `настройки`.
               Если надо подтягиваем его.
            4. Смотрим, нужно ли импортировать найденную `настройку`. Превращать строку в класс/функцию.
            5. Ставим уже готовую к работе `настройку` как атрибут текщего экземпляра настроек, и возвращаем ее.

        :param str attr: Название атрибута который ищем.

        :return: Найденный, проинициализированный(если нужно) атрибут настроект.
        :rtype: object

        """
        # TODO: ЗАКОНЧИТЬ С НАСТРОЙКАМИ!!!
        # Сначала смотрим что есть такая настройка.
        if attr not in self.__defaults:
            raise AttributeError("Invalid DRF-Auto setting: '%s'" % attr)

        # Теперь смотрим, вложенная ли настройка или нет.
        if isinstance(self.__defaults[attr], dict):
            if attr not in self.__not_create:
                # Если вложенная тогда создаем объект настроек для вложенного класса и продолжаем поиск там.
                # Обрубаем текущий уровень и пробрасываем найденные настройки для импорта след уровня.
                __imports = [
                    item.split('.', 1)[1]
                    for item in self.__imports
                    if item.split('.', 1)[0] == attr
                ]
                # Обрубаем текущий уровень и пробрасываем найденные настройки для не создания объекта след уровня.
                __not_create = [
                    item.split('.', 1)[1]
                    for item in self.__not_create
                    if item.split('.', 1)[0] == attr
                ]

                # Кэшируем значение.
                val = DRFSettings(
                    self.__defaults[attr], __imports,
                    self.__user_settings.get(attr), __not_create,
                    is_root=False
                )
                setattr(self, attr, val)
                return val

        try:
            # Смотрим поставил ли пользователь настройки.
            val = self.__user_settings[attr]
        except KeyError:
            # Если нет, возвращаем дефолтные.
            val = self.__defaults[attr]

        # Смотрим надо ли импортировать настройку.
        if attr in self.__imports:
            val = self._perform_import(val)

        # Делаем кэш атрибута, поставив его в настройки.
        setattr(self, attr, val)
        return val

    def _perform_import(self, val):
        """
        Превращает строку из настроек в классы.

        :param Union[str, iter] val: Одна или много строк с путями до классов/функций, которые нужно импортировать.

        :return: Импортированные данные.
        :rtype: Union[str, int]

        """
        if val is None:
            return None
        elif isinstance(val, six.string_types):
            return self._get_class_from_module(val)
        elif isinstance(val, (list, tuple)):
            return [self._get_class_from_module(item) for item in val]
        return val

    def _get_class_from_module(self, path_to_class):
        """
        Получение класса из модуля по пути.

        :param str path_to_class: Путь до класса, который надо импортировать.

        :return: Запрашиваемый класс.
        :rtype: class

        :raises:
            ImportError: Ошибка импорта пакета.

        """
        try:
            module_name, class_name = path_to_class.rsplit('.', 1)
            module_ = import_module(module_name)
            return getattr(module_, class_name)
        except (ImportError, AttributeError, ValueError) as e:
            msg = 'Во время импорта `{}` произошла ошибка: {}({}).'.format(path_to_class, e.__class__.__name__, e)
            logger.error(msg, exc_info=True)
            raise ImportError(msg)

    def get_code(self, code):
        """
        Возвращает объект кода.

        :param str code: Номер кода, который необходимо вернуть.

        :return: Сообщение об ошибке. соотвествующее этому коду.
        :rtype: str

        """
        return self.CODES.get('specific', {}).get(str(code))


DefaultSettings = DRFSettings()
