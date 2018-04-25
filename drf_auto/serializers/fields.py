"""
Филды для сериалайзеров.

"""
import re

from rest_framework import serializers


class GraphListMultipleChoiceField(serializers.Field):
    """
    Филд, для использования перечисления в текстовом поле. Взято из GraphQL.

    >>> from rest_framework import serializers
    >>>
    >>>
    >>> class ExampleSerializer(serializers.Serializer):
    >>>     test = GraphListMultipleChoiceField(allowed_values=['test1', 'test2'], separator=',')
    >>>
    >>> ser = ExampleSerializer({'test': 'test1,test2, test1'})
    >>> ser.is_valid()
    >>> ser.validated_data['test']
    ... ['test1', 'test2']

    """

    default_error_messages = {
        'empty_list': 'Поле пустое: `{ITEM}`.',
        'not_str': 'Поле `{TYPE}` не является строкой.',
        'find_error_char': 'Значение `{ITEM}` содержит недопустимые символы `{CHAR}`.',
        'not_found': 'Элемент `{ITEM}` недопустим. Разрешенные: `{ALLOWED}`.'
    }

    re_space = re.compile('\s')

    def __init__(self, allowed_values, separator=',', default_exclude_fields=None, required=False, *args, **kwargs):
        """
        Создаем свой филд.

        :param list allowed_values: Список разрешенных элементов.
        :param str separator: Разделитель между элементами.
        :param list default_exclude_fields: Филды, которые нужно исключить, в случае когда передано пустое значение.
        :param bool required: Обязательное ли поле.

        """
        super().__init__(*args, **kwargs)
        self.allowed_values = allowed_values
        self.separator = separator if separator else ','
        self.default_exclude_fields = default_exclude_fields if default_exclude_fields else []
        self.required = required

    def to_representation(self, obj):
        """
        Преобразуем массив значение в поле str.

        :param list obj: Список элементов, которые схлапываем.

        :return: Готовая строка.
        :rtype: str

        """
        if not obj:
            self.fail('empty_list', ITEM=obj)
        return ','.join(map(str, obj))

    def to_internal_value(self, data):
        """
        Преобразуем строку в список.

        :param str data: Исходная строка.

        :return: Список значение.
        :rtype: list

        """
        if not isinstance(data, str):
            self.fail('not_str', TYPE=type(data))

        # Возвращает все филды кроме те, что стоит исключить.
        if not data:
            return list(set(self.allowed_values) - set(self.default_exclude_fields))

        return list(set(map(self._clean_str_item, map(str, data.split(self.separator)))))

    def _clean_str_item(self, itm):
        """
        Проверяет на валидность входной элемент, обрабатывает его и возвращает.

        :param str itm: Элемент, которые необходимо обработать.

        :return: Обработанный элемент.
        :rtype: str

        """
        itm = itm.strip()
        # TODO: Вероятно, тут надо уметь и другие символы обрабатывать, типо `-`.
        if re.search(self.re_space, itm):
            self.fail('find_error_char', ITEM=itm, CHAR='Пробелы')
        if itm not in self.allowed_values:
            self.fail('not_found', ITEM=itm, ALLOWED=self.allowed_values)
        return itm


class TextToArrayField(serializers.Field):
    """
    Филд, для использования перечисления в текстовом поле. Взято из GraphQL.

    >>> from rest_framework import serializers
    >>>
    >>>
    >>> class ExampleSerializer(serializers.Serializer):
    >>>     test = TextToArrayField(separator=',')
    >>>
    >>> ser = ExampleSerializer({'test': 'test1,test2, test1'})
    >>> ser.is_valid()
    >>> ser.validated_data['test']
    ... ['test1', 'test2']

    """

    default_error_messages = {
        'empty_list': 'Поле пустое: `{ITEM}`.',
        'not_str': 'Поле `{TYPE}` не является строкой.',
        'find_error_char': 'Значение `{ITEM}` содержит недопустимые символы `{CHAR}`.',
    }

    re_space = re.compile('\s')

    def __init__(self, separator=',', required=False, *args, **kwargs):
        """
        Создаем свой филд.

        :param str separator: Разделитель между элементами.
        :param bool required: Обязательное ли поле.

        """
        super().__init__(*args, **kwargs)
        self.separator = separator if separator else ','
        self.required = required

    def to_representation(self, obj):
        """
        Преобразуем массив значение в поле str.

        :param list obj: Список элементов, которые схлапываем.

        :return: Готовая строка.
        :rtype: str

        """
        if not obj:
            self.fail('empty_list', ITEM=obj)
        return ','.join(map(str, obj))

    def to_internal_value(self, data):
        """
        Преобразуем строку в список.

        :param str data: Исходная строка.

        :return: Список значение.
        :rtype: list

        """
        if not isinstance(data, str):
            self.fail('not_str', TYPE=type(data))

        return list(set(map(self._clean_str_item, map(str, data.split(self.separator)))))

    def _clean_str_item(self, itm):
        """
        Проверяет на валидность входной элемент, обрабатывает его и возвращает.

        :param str itm: Элемент, которые необходимо обработать.

        :return: Обработанный элемент.
        :rtype: str

        """
        itm = itm.strip()
        # TODO: Вероятно, тут надо уметь и другие символы обрабатывать, типо `-`.
        if re.search(self.re_space, itm):
            self.fail('find_error_char', ITEM=itm, CHAR='Пробелы')
        if not itm:
            self.fail('empty_list', ITEM=itm)
        return itm
