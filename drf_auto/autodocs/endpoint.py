import json
import inspect

from django.contrib.admindocs.views import simplify_regex
from django.utils.encoding import force_str

from rest_framework.fields import ChoiceField, SerializerMethodField
from rest_framework.viewsets import ModelViewSet
from rest_framework.serializers import BaseSerializer, ListSerializer

from .settings import DocsSettings

# Список методов у ViewSets. Надо для добычи разрешенных методов у этих классов.
VIEWSET_METHODS = {
    'List': ['get', 'post'],
    'Instance': ['get', 'put', 'patch', 'delete'],
}

# Методы по типу сериалайзера. Нужно для авторазруливания.
SERIALIZER_METHODS = {
    'IN': ('GET', 'ALL'),
    'OUT': ('POST', 'PUT', 'PATCH', 'DELETE', 'ALL'),
    'ALL': ('ALL', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE')
}


class ApiEndpoint(object):
    def __init__(self, pattern, parent_regex=None, drf_router=None):
        """
        Полная инициализация поинта. Тут доатсаются и формируются все данные.

        :param pattern:
        :param parent_regex:
        :param drf_router:

        """
        self.drf_router = drf_router
        self.pattern = pattern
        self.callback = pattern.callback
        self.docstring = self.__get_docstring(self.callback.cls)
        self.name_parent = simplify_regex(parent_regex).strip('/') if parent_regex else None
        self.path = self.__get_path(parent_regex)
        self.allowed_methods = self.__get_allowed_methods()

        self.errors = None
        self.serializer_classes = self.__get_serializer_classes(DocsSettings.SERIALIZERS_ATTR_NAME)
        self.methods_docs = {}  # Тут лежат докстринги функций классов.
        self.exclude_fields = self.__get_exclude_fields(DocsSettings.EXCLUDE_FIELDS_ATTR_NAME)

        if self.serializer_classes:
            fields_in, fields_out = {}, {}
            for method_name, data in self.serializer_classes.items():
                # TODO: Тут строгий дубляж логики над разными контейнерами. Вынести в одну общую функцию.
                # Сначала достаем филды, которые надо исключить из этого сериалайзера.
                exc_f_in, exc_f_out, exc_f_all = [], [], self.exclude_fields.get(method_name)
                # Если указаны для разных типов запросов.
                if isinstance(exc_f_all, dict):
                    __exc_f_in = exc_f_all.get('in', exc_f_all.get('IN', []))
                    __exc_f_out = exc_f_all.get('out', exc_f_all.get('OUT', []))
                    if isinstance(__exc_f_in, (list, tuple, set)):
                        exc_f_in = __exc_f_in
                    if isinstance(__exc_f_out, (list, tuple, set)):
                        exc_f_out = __exc_f_out
                # Если указаны для одного типа запросов.
                elif not isinstance(exc_f_all, (list, tuple, set)):
                    exc_f_all = []

                # Смотрим, прописал ли программист для доки классы или нет.
                if isinstance(data, dict):
                    ser_in = data.get('IN', data.get('in', None))
                    __exc_f_in = exc_f_in if exc_f_in else exc_f_all
                    __exc_f_out = exc_f_out if exc_f_out else exc_f_all
                    fields_in[method_name] = self.__get_serializer_fields(ser_in, __exc_f_in) if ser_in else {}
                    ser_out = data.get('OUT', data.get('out', None))
                    fields_out[method_name] = self.__get_serializer_fields(ser_out, __exc_f_out) if ser_out else {}
                else:
                    # Если не прописал, пробуем руками разрулить что куда.
                    if method_name in SERIALIZER_METHODS['IN'] and 'GET' in self.allowed_methods:
                        __exc_f_in = exc_f_in if exc_f_in else exc_f_all
                        fields_out[method_name] = self.__get_serializer_fields(data, __exc_f_in)
                    if method_name in SERIALIZER_METHODS['OUT'] and \
                            set(SERIALIZER_METHODS['OUT']) & set(self.allowed_methods):
                        __exc_f_out = exc_f_out if exc_f_out else exc_f_all
                        fields_in[method_name] = self.__get_serializer_fields(data, __exc_f_out)

                doc = self.__get_docstring(getattr(self.callback.cls, method_name.lower(), None))
                if doc:
                    self.methods_docs[method_name] = doc

            self.fields = {
                'IN': fields_in, 'OUT': fields_out
            }

        self.permissions = self.__get_permissions_class()
        self.json_fields = self.__get_serializer_fields_json()

    def __get_path(self, parent_regex):
        """
        Формирует и возвращает полный путь до поинта относительно урлов.

        :param parent_regex: Родительский урл.
        :type parent_regex: RegexpURL

        :return: Полный путь относительно роутера до поинта.
        :rtype: str

        """
        if parent_regex:
            return '/{0}{1}'.format(self.name_parent, simplify_regex(self.pattern.regex.pattern))
        return simplify_regex(self.pattern.regex.pattern)

    def is_method_allowed(self, callback_cls, method_name):
        """
        Проверяет рахрешен ли данный метод.

        :param callback_cls: Класс поинта.
        :param method_name: Название метода.

        :return: Результат проверки.
        :rtype: bool

        """
        has_attr = hasattr(callback_cls, method_name)
        viewset_method = (issubclass(callback_cls, ModelViewSet) and
                          method_name in VIEWSET_METHODS.get(self.callback.suffix, []))

        return has_attr or viewset_method

    def __get_allowed_methods(self):
        """
        Возвращает список разрешенных методов.

        :return: Список размешеных методов у поинта.
        :rtype: list

        """
        viewset_methods = []
        if self.drf_router:
            for prefix, viewset, basename in self.drf_router.registry:
                if self.callback.cls != viewset:
                    continue

                lookup = self.drf_router.get_lookup_regex(viewset)
                routes = self.drf_router.get_routes(viewset)

                for route in routes:

                    # Only actions which actually exist on the viewset will be bound
                    mapping = self.drf_router.get_method_map(viewset, route.mapping)
                    if not mapping:
                        continue

                    # Build the url pattern
                    regex = route.url.format(
                        prefix=prefix,
                        lookup=lookup,
                        trailing_slash=self.drf_router.trailing_slash
                    )
                    if self.pattern.regex.pattern == regex:
                        funcs, viewset_methods = zip(
                            *[(mapping[m], m.upper())
                              for m in self.callback.cls.http_method_names
                              if m in mapping]
                        )
                        viewset_methods = list(viewset_methods)
                        if len(set(funcs)) == 1:
                            self.docstring = inspect.getdoc(getattr(self.callback.cls, funcs[0]))

        view_methods = [force_str(m).upper()
                        for m in self.callback.cls.http_method_names
                        if self.is_method_allowed(self.callback.cls, m)]
        return sorted(viewset_methods + view_methods)

    def __get_docstring(self, obj):
        """
        Возвращает docstring объекта.

        :param obj: Объект, для которого надо верйнть докстринг.
        :type obj: object

        :return: Докстринг объекта.
        :rtype: str

        """
        return inspect.getdoc(obj)

    def __get_permissions_class(self):
        """
        Возвращает список классов с правами.

        :return: Список классов с пермишенами.
        :rtype: list

        """
        for perm_class in self.pattern.callback.cls.permission_classes:
            return perm_class.__name__

    def __get_serializer(self):
        """
        Возвращает проинициализированный сериалайзер для поинта.

        :return: Сериалайзер поинта.
        :rtype: rest_framework.serializers.Serializer

        """
        try:
            return self.serializer_class()
        except KeyError as e:
            self.errors = e

    def __get_serializer_class(self):
        """
        Возвращает сериалайзер для поинта.

        :return: Сериалайзер для поинта.
        :rtype: rest_framework.serializers.Serializer()

        """
        if hasattr(self.callback.cls, 'serializer_class'):
            return self.callback.cls.serializer_class

        if hasattr(self.callback.cls, 'get_serializer_class'):
            return self.callback.cls.get_serializer_class(self.pattern.callback.cls())

    def __get_exclude_fields(self, attr_name):
        """
        Возвращает словарь с полями, которые необходимо исключить из доки.

        :return: Словарь с ключами, в формате как и с филдами.
        :rtype: dict

        """
        if hasattr(self.callback.cls, attr_name) and isinstance(getattr(self.callback.cls, attr_name), dict):
            return {
                key.upper(): val for key, val in getattr(self.callback.cls, attr_name).items()
            }

        return {}

    def __get_serializer_classes(self, attr_name):
        """
        Возвращает словарь сериалайзеров у поинта.

        :param str attr_name: Название атрибута для поиска сериалайзеров.


        :return: Словарь сериалайзеров. Ключ это метод, значение сериалайзер.
        :rtype: dict

        """
        # Если программист позаботился о доке.
        if hasattr(self.callback.cls, attr_name) and isinstance(getattr(self.callback.cls, attr_name), dict):
            return {
                key.upper(): val for key, val in getattr(self.callback.cls, attr_name).items()
            }

        # Если программист не позаботился о доке, или сериалайзер и вправду один.
        if hasattr(self.callback.cls, 'serializer_class'):
            return {'ALL': self.callback.cls.serializer_class}
        if hasattr(self.callback.cls, 'get_serializer_class'):
            return {'ALL': self.callback.cls.get_serializer_class(self.pattern.callback.cls())}

    def __get_serializers_fields(self):
        """
        Формирует и возвращает списки филдов по сериалайзерам.

        :return: Словарь, где ключь это метод, значение список филдов.
        :rtype: dict

        """
        fields = {}

        for method_name, serializer_class in self.serializer_classes.items():
            fields[method_name] = self.__get_serializer_fields(serializer_class())

        return fields

    def __get_field_props(self, field, key=None, sub_fields=None,
                          to_many_relation=None, label=None, choices_fields=None):
        """
        Формирует данные по конкретному филду.

        :param rest_framework.fields.Field, rest_framework.serializers.Serializer field: Объект филда.
        :param str key: Название филда.
        :param list sub_fields: Вложенные филды, если это составной филд.
        :param bool to_many_relation: Указатель на Relation связи.
        :param str label: Текст описания филда label поле.
        :param tuple choices_fields: Значения, которые может принимать это поле.

        :return: Словарь с данными по конкретному филду.
        :rtype: dict

        """
        return {
            # Если нет field_name [предположительно] это корневой список без имени
            'name': key if key is not None else (field.field_name if field.field_name else '[list]'),
            'type': str(field.__class__.__name__),
            'sub_fields': sub_fields,
            'required': field.required,
            'to_many_relation': to_many_relation if to_many_relation is not None else hasattr(field, 'many'),
            'label': label if label else field.label if field.label else '',
            'description': field.help_text if field.help_text else '',
            'choices_fields': choices_fields
        }

    def __get_serializer_fields(self, serializer, exclude_fields=None):
        """
        Возвращает список фидлов у сериалайзера.

        :param serializer: Сериалайзер, для которого необъходимо вернуть.
        :param exclude_fields: Поля, которые необходимо исключить из сериалайзера.
        :type serializer: rest_framework.serializers.Serializer, rest_framework.serializers.SerializerMetaclass
        :type exclude_fields: list

        :return: Список филдов сериалайзера.
        :rtype: list

        """
        fields = []
        if not serializer:
            return []
        # На сто процентов убеждаемся, что пришел проинициализированный сериалайзер.
        serializer = serializer if isinstance(serializer, BaseSerializer) else serializer()
        extra_fields = getattr(getattr(serializer, 'Meta', {}), DocsSettings.SERIALIZER_DOC_ATTR, {})

        if isinstance(serializer, ListSerializer):
            # Обрабатываем список
            fields.append(self.__get_field_props(
                serializer, sub_fields=self.__get_serializer_sub_fields(serializer)))

        if hasattr(serializer, 'get_fields'):
            for key, field in serializer.get_fields().items():
                if exclude_fields and key in exclude_fields:
                    continue

                label = None

                if extra_fields and isinstance(field, SerializerMethodField):
                    # Пробуем достать из мета класса.
                    ser = extra_fields.get(key, None)
                    if ser:
                        label = field.label
                        field = ser()

                to_many_relation = True if hasattr(field, 'many') else False
                sub_fields = self.__get_serializer_sub_fields(field)
                choices_fields = None

                if isinstance(field, ChoiceField):
                    choices_fields = field.choices

                fields.append(self.__get_field_props(
                    field, key=key, sub_fields=sub_fields,
                    to_many_relation=to_many_relation, label=label,
                    choices_fields=choices_fields
                ))

        return fields

    def __get_serializer_sub_fields(self, field):
        """
        Достает вложенные филды у филда.

        :param field: Объект филда.
        :type field: rest_framework.fields.Field или rest_framework.serializers.Serializer

        :return: Список со вложенными филдами.
        :rtype: list

        """
        sub_fields = None
        if isinstance(field, BaseSerializer):
            if hasattr(field, 'many'):
                if isinstance(field.child, BaseSerializer):
                    sub_fields = self.__get_serializer_fields(field.child)
                elif isinstance(field, ListSerializer):
                    sub_fields = [self.__get_field_props(field.child, key='[list-item]')]
            else:
                sub_fields = self.__get_serializer_fields(field)
        return sub_fields

    def __get_serializer_fields_json(self):
        """
        Делаем JSON для автодоки.

        """
        # TODO: Пока заглушка.
        return json.dumps([{'name': 'CharField'}])
