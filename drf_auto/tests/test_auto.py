import logging

from django.contrib.auth import get_user_model
from django.db import models

from rest_framework import serializers
from rest_framework.test import APITestCase

from ..autodocs.docs import ApiDocumentation

from .utils import Deferred

log = logging.getLogger(__name__)

"""
При подготовке данных для запроса не всегда ясно какие нужны значения к примеру в случае
с такими полями как JSONField или когда IntegerField используется как PK экземпляра модели.

Для таких ситуаций нужно использовать функцию `apps.utils.tests.test_helper_factory`.
При необходимости наличия среди данных pk использовать класс `apps.utils.tests.Deferred`.
Подробнее в docstring'ах функции и класса.

Так же view можно дополнить классовым методом test_setup для подготовки к его тестированию.
В аргументах к методу передается экземпляр класса AutoTestCase.

И методом test_prepare_request, аргументы которого экземпляр тестового класса, данные и формат запроса.
В ответе от test_prepare_request должен приходить словарь со всеми именнованными аргументами для запроса.

"""


def get_serializer(endpoint, method_name, dict_key='in'):
    """
    Возвращает класс сериалайзера, если тот есть для данного поинта и метода.

    :param `ApiEndpoint` endpoint: Поинт.
    :param str method_name: Метод.
    :param str dict_key: Ключ словаря с сериалайзерами, либо 'in' либо 'out'.

    :return: Класс сериалайзера либо None.

    """
    methods = [method_name]
    # Если тестируем PATCH метод и при этом для него нет сериалайзера, используем сериалайзер от PUT.
    if method_name == 'PATCH':
        methods.append('PUT')

    for method in methods:
        if method in endpoint.serializer_classes and \
            isinstance(endpoint.serializer_classes[method], dict) and \
                dict_key in endpoint.serializer_classes[method]:
            return endpoint.serializer_classes[method][dict_key]


def resolve_deferred(value):
    """
    Заменяет `Deferred` объект на pk экземпляра модели `Deferred.model`.

    :param any value: Любой объект.

    """
    if isinstance(value, Deferred):
        obj = model_instance(value.model, value.force_create)
        return obj.pk
    elif isinstance(value, dict):
        return {resolve_deferred(k): resolve_deferred(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_deferred(v) for v in value]
    return value


def model_instance(model, force_create=False):
    """
    Создание и получение экземпляра модели.

    :param any model: Модель.
    :param bool force_create: Не получать имеющийся объект, а создавать новый.

    :return: Экзмепляр модели.
    :rtype: models.Model.

    """
    if not force_create and model.objects.all().count() > 0:
        return model.objects.first()

    data = {}
    for field in model._meta.get_fields():
        if not field.auto_created and not field.blank:
            if hasattr(field, 'choices') and len(field.choices) > 0:
                data[field.name] = field.choices[0][0]

            elif isinstance(field, models.IntegerField):
                data[field.name] = 1

            elif isinstance(field, models.ForeignKey):
                data[field.name] = model_instance(field.related_model)

            elif isinstance(field, models.CharField):
                data[field.name] = 'test'
    return model.objects.create(**data)


class AutoTestCase(APITestCase):
    """
    Класс для автоматического тестирования REST ручек.

    """
    @classmethod
    def setUpClass(cls):
        """
        Создание пользователя для всех тестов, который цепляется через `settings.AUTH_USER_PK`

        """
        super(AutoTestCase, cls).setUpClass()
        model_instance(get_user_model())

    def setUp(self):
        """
        Подготовка к тестовому запросу, получение данных из словаря REQUESTS_DATA
        и создание / получение необходимых объектов, ключи которых используются в URL.

        """
        self.endpoint, self.method, self.serializer, self.request_type = REQUESTS_DATA.get(self._testMethodName)

        path = self.endpoint.path

        if '<pk>' in path:
            obj = model_instance(self.endpoint.callback.cls.queryset.model)
            path = path.replace('<pk>', str(obj.pk))

        self.path = path

        if hasattr(self.endpoint.callback.cls, 'test_setup'):
            getattr(self.endpoint.callback.cls, 'test_setup')(self)

    def base_test_method(self):
        """
        Метод, который проверяет полученный от итератора endpoint.

        """
        request_method = getattr(self.client, self.method.lower())

        if self.serializer:
            if self.request_type == 'all':
                # Запрос со всеми данными на входе.
                data = self.prepare_request_data(self.serializer)
                response = self.send_request(request_method, self.path, data, 'json')
                self.check_response_is_valid(response)

            elif self.request_type == 'only_required':
                # Запрос только с обязательными данными.
                data = self.prepare_request_data(self.serializer, only_required=True)
                response = self.send_request(request_method, self.path, data, 'json')
                self.check_response_is_valid(response)

            elif self.request_type == 'without_required':
                # Запрос не со всеми обязательными данными.
                data = self.prepare_request_data(self.serializer, only_required=True)
                data.popitem()
                response = self.send_request(request_method, self.path, data, 'json')
                self.assertTrue(400 <= response.status_code < 500)

        else:
            # Запрос без данных на входе.
            response = self.send_request(request_method, self.path)
            self.check_response_is_valid(response)

    def prepare_request_data(self, field, only_required=False):
        """
        Подготавливает данные для запроса.

        :param rest_framework.fields.Field, rest_framework.serializers.Serializer field: Объект филда или сериалазейра.
        :param bool only_required: Использовать ли только обязательные поля.

        :return: Данные для отправки клиентом.
        :rtype: list, dict.

        """
        # Если это класс сериалайзера, а не его экземпляр.
        if isinstance(field, serializers.SerializerMetaclass):
            return self.prepare_request_data(field())

        # Либо имеется тестовое значение установленное через `test_helper_factory`.
        elif hasattr(field, 'test_helper_value'):
            return resolve_deferred(field.test_helper_value)

        # Либо это список.
        elif isinstance(field, serializers.ListSerializer):
            return [self.prepare_request_data(field.child)]

        # Либо это экземпляр сериалайзера.
        elif isinstance(field, serializers.BaseSerializer):
            return {
                k: self.prepare_request_data(v)
                for k, v in field.get_fields().items()
                if (not only_required) or (only_required and v.required)
            }

        # Либо это поле.
        elif isinstance(field, serializers.ChoiceField):
            for val, verbose in field.choices.items():
                return val

        elif isinstance(field, serializers.PrimaryKeyRelatedField):
            return model_instance(field.queryset.model).pk

        elif isinstance(field, serializers.CharField):
            return 'test'

        elif isinstance(field, serializers.IntegerField):
            return 1

    def send_request(self, request_method, path, data=None, format_type=None):
        """
        Отправляет запрос.

        :param method request_method: Метод клиента.
        :param str path: URL.
        :param dict data: Данные для запроса.
        :param str format_type: Формат данных.

        :return: Ответ.
        :rtype: `rest_framework.response.Response`.

        """
        kwargs = dict(data=data, format=format_type)
        if hasattr(self.endpoint.callback.cls, 'test_prepare_request'):
            kwargs = getattr(self.endpoint.callback.cls, 'test_prepare_request')(self, **kwargs)

        self.data = data
        print_strings = ['Отправка {} на {}'.format(request_method.__name__, path)]
        if data is not None:
            print_strings.append('с данными')
        log.debug(' '.join(print_strings + ['\n']))
        return request_method(path, **kwargs)

    def check_response_is_valid(self, response):
        """
        Проверяет ответ на успешность и корректность.

        :param `rest_framework.response.Response` response: Ответ.

        """
        # if not (200 <= response.status_code < 400):
        #     import pdb; pdb.set_trace()
        self.assertTrue(200 <= response.status_code < 400)

        response_serializer = get_serializer(self.endpoint, self.method, 'out')
        if response_serializer:
            self.check_response_data(response.data, response_serializer)

    def check_response_data(self, data, field):
        """
        Проверяем данные в ответе.

        :param any data: Словарь `Response.data` либо одно из его значений.
        :param any field: Сериалайзер или поле для сравнения данных в ответе.

        """
        # @TODO: Проверка с помощью данных сериалайзера на данный момент не возможна
        # т.к. что-то происходит с QuerySet'ом из-за чего serializer.data вызывает RuntimeError.
        '''
        if method_name == 'POST' and method_name in self.endpoint.serializer_classes and \
                'out' in self.endpoint.serializer_classes[method_name]:
            serializer = self.endpoint.serializer_classes[method_name]['out'](
                self.endpoint.callback.cls.queryset, many=True)
            self.assertEqual(response.data, serializer.data)
        '''
        # Если это класс сериалайзера, а не его экземпляр.
        if isinstance(field, serializers.SerializerMetaclass):
            return self.check_response_data(data, field())

        '''
        if 'results' in data and 'count' in data:
            for item in data['results']:
                self.check_response_data(item, out_fields)

        else:
            for field_name, value in data.items():
                try:
                    field_data = fields[field_name]
                except:
                    import pdb; pdb.set_trace()
                # Проверка наличия филда среди ожидаемых в ответе
                self.assertTrue(field_name in available_fields)
                available_fields.remove(field_name)

                if field_name in required_fields:
                    required_fields.remove(field_name)

                if field_data['sub_fields']:
                    if hasattr(field_data['field_instance'], 'test_helper_as_dict'):
                        for key, item in data[field_name].items():
                            self.check_response_data(item, field_data['sub_fields'])
                    else:
                        self.check_response_data(data[field_name], field_data['sub_fields'])

                else:
                    field_instance = field_data['field_instance']

                    # Проверка значения если филд обязателен или имеется значение в ответе
                    if field_data['required'] or value is not None:
                        # Проверка типа филда
                        self.assertEquals(type(field_instance.to_representation(value)), type(value))

                        # Проверка коррекности значения (иначе возникнет исключение)
                        # self.assertRaises(ValidationError, field_instance.to_internal_value(value))
                        field_instance.to_internal_value(value)

            # Проверяем чтобы все обязательные поля в ответе были
            self.assertEqual(len(required_fields), 0)
        '''


ENDPOINTS = ApiDocumentation().get_endpoints()

# Проверяем пока вьюхи концепт мапы.
ENDPOINTS = [ep for ep in ENDPOINTS if ep.path.startswith('/api/maps/concept-map/')]

# Собираем список запросов.
REQUESTS_LIST = []
for endpoint in ENDPOINTS:
    for method in endpoint.allowed_methods:
        serializer = get_serializer(endpoint, method)
        if serializer:
            # @TODO: Доработать тестирование без обязательных данных в запросе (without_required).
            # for request_type in ('all', 'only_required', 'without_required'):
            for request_type in ('all', 'only_required'):
                REQUESTS_LIST.append((endpoint, method, serializer, request_type))
        else:
            REQUESTS_LIST.append((endpoint, method, serializer, None))

REQUESTS_DATA = {}
# Добавляем для них тестовые методы.
for endpoint, method, serializer, request_type in REQUESTS_LIST:
    method_name = 'test_{}_{}_{}'.format(endpoint.callback.__name__, method, request_type)
    REQUESTS_DATA[method_name] = (endpoint, method, serializer, request_type)
    setattr(AutoTestCase, method_name, AutoTestCase.base_test_method)
