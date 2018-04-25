"""
Авто генерики для REST API.

"""
import logging

from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, UpdateAPIView,
    CreateAPIView, DestroyAPIView, GenericAPIView
)
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, ValidationError

from ..exceptions import FailPointRequest
from ..settings import DefaultSettings


logger = logging.getLogger(__name__)


class AutoPointFailRequest(GenericAPIView):
    """
    Класс, для автоматической обработки ошибок.
    Он предоставляет предоставляет метод, который формирует и возвращает объект ответа с ошибкой.
    Так же, он отлавливает след ошибки и обрабатывая их отдает ответ клиенту.
        * FailPointRequest - Ошибка во время запроса. Обработка аналогична методу fail.

    Наследуемся от GenericAPIView, что бы были дефолтные методы для автореста.

    """
    def fail(self, status, code=None, message=None, data=None, fields=None):
        """
        Метод, для автоответа с ошибкой.

        :param int status: Код ответа от сервера.
        :param int code: Код, который вернется в параметре `code`. По дефолту `code` = `status`.
        :param str message: Сообщение, которое переопределит стандартное для `code`. По дефолту стандартное сообщение.
        :param dict data: Доп данные которые вернуться в запросе. Добавляются только если указаны или есть в fields.
        :param dict fields: Словарь филдов, для управления ответом.
                            Ключ это ключ который вернется, значение, это ключ из стандартного набора атрибутов.
                            Пример: {'response_code': 'code', 'response_message': 'message'}.
                            В таком случае ответ всегда будет фиксирован и выглядеть так:
                            {'response_code': code, 'response_message': message}. Вне зависимости от доп данных.

        :return: Ответ сервера об ошибке.
        :rtype: django.http.HttpResponse

        """
        if not isinstance(status, int):
            raise TypeError('Неверный тип для status. Ожидался int.')

        code = code if code else status
        if not message:
            message = DefaultSettings.DOCS.get_code(code)

        kwargs = {}  # Формируем ответ.
        if fields:
            # Если нужно ручное управление филдами.
            kwargs = {new_key: locals().get(old_key) for new_key, old_key in fields.items()}
        else:
            # Иначе формируем стандартный ответ.
            kwargs = {'code': code, 'message': message}
            if data:
                kwargs['data'] = data

        # TODO: Научиться устанавливать самостоятельно формат ответа в случае fail. Через настройки приложения.
        return Response(data=kwargs, status=status)

    def handle_exception(self, exc):
        """
        Переопределяем обработку исключений, что отловить наше.

        """
        # TODO: Добавить поддержку замены этой функции на пользовательскую. Через настройки приложения и importlib.
        # TODO: Добавить поддержку выключения этой фичи.
        # Нужно что бы пользователь сам управлял, какие части приложения ему нужны.
        if isinstance(exc, FailPointRequest):
            return self.fail(status=exc.status, code=exc.code, message=exc.message, data=exc.data, fields=exc.fields)
        if isinstance(exc, ValidationError):
            return self.fail(status=400, code=401, data=exc.detail)

        return super().handle_exception(exc)


class AutoSearchSerializerView(AutoPointFailRequest):
    """
    Класс для автомагического поиска сериалайзера для обработки запроса и обработки ответа.
    Сначала пробует достать конкретный сериалайзер для этого метода,
    Из поля serializer_classes: dict. Если такого нет, то берет дефолтный для этого метода сериалайзер.

    """
    # serializer_classes
    # Хватаем из настроек и ставим атрибуты для автореста во вьюху.
    serializers_response_field = DefaultSettings.SERIALIZERS_RESPONSE_FIELD
    serializers_request_field = DefaultSettings.SERIALIZERS_REQUEST_FIELD
    serializers_request_key = DefaultSettings.SERIALIZERS_REQUEST_KEY
    serializers_response_key = DefaultSettings.SERIALIZERS_RESPONSE_KEY

    def __preparation_request_method(self):
        """
        Подготовка метода для поиска нужного сериалайзера.
        Формирует список методов которые будем искать.
        Список, потому что какие то метоы могут быть равнозначны. Put/Path

        :return: Список методов.
        :rtype: list

        """
        method = self.request.method.lower()
        methods = [method]
        # Если метод PATCH/PUT, но для него нет сериалайзеров, использовать сериалайзеры для PUT/PATCH.
        if method == 'patch':
            methods.append('put')
        if method == 'put':
            methods.append('patch')

        return methods

    def __get_serializers_for_search(self, is_response=False):
        """
        Ищет и возвращаем словарь сериалайзеров, в котором будем искать нужный нам.

        :param bool is_response: Это вызов функции для ответа АПИ?

        :return: Словарь с сериалайзерами, который описал пользвователь.
        :rtype: dict

        """
        if is_response:
            return getattr(self, self.serializers_response_field, None)
        else:
            return getattr(self, self.serializers_request_field, None)

    def __search_serializers_in_dict(self, dict_serializers, methods, type_search):
        """
        Поиск нужного сериалайзера в dict_serializers, подходящего под methods и type_search.

        :param dict dict_serializers: Словарь с сериалайзерами, который описал пользователь.
        :param iter methods: Список методов, которые мы ищем.
        :param str type_search: Тип поиска. Ищем сериалайзер для входящих данных или исходящих?

        dict_serializer : {get: {in: ser, OUT: ser}, post: ser,...}

        :return: Найденный сериалайхзер или None.
        :rtype: rest_framework.serializers.BaseSerializer()

        """
        result = None

        # Ради гибкости использования, приходиться итерировать не по методам и искать в словаре,
        # а итерировать по словарю и искать в методах.

        # TODO: python2
        for _method, _serializer in dict_serializers.items():
            if _method.lower() in methods:
                if isinstance(_serializer, dict):
                    # TODO: python2
                    for _view_types, _view_ser in _serializer.items():
                        if _view_types.lower() == type_search.lower():
                            result = _view_ser
                            break
                else:
                    result = _serializer
                break

        return result

    def get_serializer_class(self, is_response=False):
        """
        Пробуем достать необходимый сериалайзер исходя из атрибутов класса.

        :param bool is_response: Это вызов функции для ответа АПИ?

        :return: Найденный класс сериалайзера.
        :rtype: rest_framework.serializers.BaseSerializer()

        """
        result_serializer = None  # Тут будет найденный сериалайзер.
        # Тип сериалайзера. Для входящих данных или исходящих.
        type_search = self.serializers_response_key if is_response else self.serializers_request_key

        # Достаем сериалайзеры для поиска нужного, в зависимости от типа вызова функиции.
        serializers = self.__get_serializers_for_search(is_response=is_response)

        # Если описание ввиде словаря, тогда надо в словаре искать.
        if serializers and isinstance(serializers, dict):
            # Ищем в словаре описанном пользователем.
            methods = self.__preparation_request_method()
            result_serializer = self.__search_serializers_in_dict(serializers, methods, type_search)

        # Иначе, если нет описание словарем, а есть просто сериалайзер, его и возвращаем.
        elif isinstance(serializers, BaseSerializer):
            result_serializer = serializers

        if result_serializer and issubclass(result_serializer, BaseSerializer):
            return result_serializer

        # Если нашли, то возвращаем.
        return super().get_serializer_class()


# TODO: Было бы классно, убрать это APIView и сделать классы миксинами, или чем то аналогичным.
class AutoResponseSerializerView(AutoSearchSerializerView):
    """
    Класс, который помогает автомагически формировать респонс от сервера.
    Сначала пробует достать конкретный сериалайзер для этого метода,
    Из поля serializer_classes: dict. Если такого нет, то берет дефолтный для этого метода сериалайзер.
    is_serializer: Полу, указывающее нужно ли оборачивать ответ в сериалайзер или он уже в готовом dict.

    """
    is_serializer = False

    def get_response(self, code, serializer=None, data=None, is_serializer=False,
                     serializer_class=None, many=False, *args, **kwargs):
        """
        Возвращет объект Response в правильном формате.
        Если передан serializer тогда он будет истинным ответом.
        Иначе берем data. Если передан serializer_class, тогда дата оборачивается в него.
        Иначе пробует по умному найти сериалайзер для этого ответа.
        Если is_serializer = True, тогда дата возвращается в том виде, в котором передана.

        :param int code: Код ответа ручки
        :param rest_framework.serializers.Serializer serializer: Сериалайзер, ктоорый уже хранит данные.
        :param dict data: Словарь ответа от сервера.
        :param bool is_serializer: Серилизованные ли данные пришли.
        :param rest_framework.serializers.Serializer() serializer_class: Класс сериалайзера, которым отдать респонс.
        :param bool many: Один или несколько объектов.
        :param tuple args: аргументы для формирования Response кроме status и data
        :param dict kwargs: аргументы для формирования Response кроме status и data

        :return: Response(data=data, status=code, *args, **kwargs)

        """
        # TODO: Добавить status в параметры. Он будет код ответа сервера, а code код ответа в JSON.
        # ПО дефолтну пусть определяет из типа запроса. get-200,post-201,put/patch-200,delete-204
        result_data = None
        # TODO: Странная логика if data and if serializer. Кажется это взаимозаменяемые вещи.
        if data:
            if serializer:
                result_data = serializer.data
            elif is_serializer:
                result_data = data
            elif serializer_class:
                result_data = serializer_class(data, many=many).data
            else:
                result_data = self.get_serializer_class(is_response=True)(data, many=many).data

        return Response(data=result_data, status=code)


class AutoRequestSerializerView(AutoPointFailRequest):
    """
    Класс, который помогает автомагически выбирать сериалайзер для обработки входящего и исходящего запроса.

    """
    def get_initial_data(self, data):
        """
        Интерфейс для изменения данных передаваемых сериалайзеру.

        :param dict data: Данные полученные в запросе.

        :return: Возвращаемые данные.
        :rtype: dict

        """
        return data

    def get_serializer(self, *args, **kwargs):
        """
        Переопределяем, что бы дать возможность менять данные перед обработкой запроса.

        :param tuple args: Позиционные аргументы для сериалайзера.
        :param dict kwargs: Именованные аргументы для сериалайзера.

        :return: Проинициализированный найденный сериалайзер.
        :rtype: rest_framework.serializers.BaseSerializer

        """
        if 'data' in kwargs:
            kwargs['data'] = self.get_initial_data(kwargs['data'])
        return super().get_serializer(*args, **kwargs)


class RestAPIView(AutoRequestSerializerView, AutoResponseSerializerView):
    """
    Стандартный APIView с AutoRequest и AutoResponse.

    """
    pass


# TODO: Доразобраться с пагинацией.
class RestListAPIView(AutoRequestSerializerView, ListAPIView, AutoResponseSerializerView):
    """
    Генерик для списка объектов.

    """
    def get(self, request, *args, **kwargs):
        """
        Список объектов.

        """
        return super().get(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            # TODO: Тут в queryset падают данные, с оберткой пагинации.
            queryset = self.get_paginated_response(queryset)
            return self.get_response(code=200, data=queryset, many=True, is_serializer=True)

        return self.get_response(code=200, data=queryset, many=True, is_serializer=self.is_serializer)

    def get_paginated_response(self, data):
        """
        Переопределяем логику, что бы сформировать и вернуть обернутые в пагинацию данные.

        :param django.db.models.QuerySet data: Данные которые пришли.

        """
        assert self.paginator is not None
        # TODO: Приходиться формировать объект ответа два раза,
        # что бы оставить свободу выбора юзеру, в выборе пагинационного бэкенда.
        # TODO: Костыль определяния, пришли уже конкретный филды или объект целиком?
        # Если конкретные, то серилизовать их не нужно.
        # TODO: Неверное суждение.
        ser_data = data
        if not getattr(data, '_fields', None):
            ser_data = self.get_serializer_for_response()(data, many=True).data
        return self.paginator.get_paginated_response(ser_data).data


class RestRetrieveAPIView(AutoRequestSerializerView, RetrieveAPIView, AutoResponseSerializerView):
    """
    Генерик для одного объекта.

    """
    def get(self, request, *args, **kwargs):
        """
        Возвращает объект.

        """
        return super().get(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.get_response(code=200, data=serializer.data, is_serializer=True)


class RestUpdateAPIView(AutoRequestSerializerView, UpdateAPIView, AutoResponseSerializerView):
    """
    Генерик для редактирования объекта.

    """
    def put(self, request, *args, **kwargs):
        """
        Обновляет объект.

        """
        return super().put(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """
        Частично обновляет объект.

        """
        return super().patch(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return self.get_response(code=200, data=instance)


class RestCreateAPIView(AutoRequestSerializerView, CreateAPIView, AutoResponseSerializerView):
    """
    Генерик для создания объекта.

    """
    def post(self, request, *args, **kwargs):
        """
        Создание объекта.

        """
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return self.get_response(code=201, data=serializer.instance, headers=headers)


class RestDestroyAPIView(AutoRequestSerializerView, DestroyAPIView, AutoResponseSerializerView):
    """
    Генерик для удаления объекта.

    """
    def delete(self, request, *args, **kwargs):
        """
        Удаление объекта.

        """
        return super().delete(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.get_response(code=204)
