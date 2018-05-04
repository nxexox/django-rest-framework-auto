"""
Парсеры для автодоки.

"""
from rest_framework import serializers

from ..settings import DefaultSettings


class BaseParser(object):
    """
    Базовый интерфейс парсера.

    """
    def __init__(self, serializer_class=None, *args, **kwargs):
        """
        :param rest_framework.serializers.BaseSerializer serializer_class: Класс сериалайзера, который парсим.

        """
        self.serializer_class = serializer_class

    def get_serializer_fields(self, serializer, exclude_fields=None, *args, **kwargs):
        """
        Возвращает список фидлов у сериалайзера.

        :param rest_framework.serializers.Serializer serializer: Сериалайзер, для которого необъходимо вернуть.
        :param iter exclude_fields: Поля, которые необходимо исключить из сериалайзера.

        :return: Список филдов сериалайзера.
        :rtype: iter

        """
        raise NotImplementedError

    def get_serializer_sub_fields(self, field, *args, **kwargs):
        """
        Достает вложенные филды у филда.

        :param rest_framework.fields.Field rest_framework.serializers.Serializer field: Объект филда.

        :return: Список со вложенными филдами.
        :rtype: iter

        """
        raise NotImplementedError

    def get_field_props(self, field, key=None, sub_fields=None,
                        to_many_relation=None, label=None, choices_fields=None, *args, **kwargs):
        """
        Формирует данные по конкретному филду.

        :param rest_framework.fields.Field rest_framework.serializers.Serializer field: Объект филда.
        :param str key: Название филда.
        :param list sub_fields: Вложенные филды, если это составной филд.
        :param bool to_many_relation: Указатель на Relation связи.
        :param str label: Текст описания филда label поле.
        :param tuple choices_fields: Значения, которые может принимать это поле.

        :return: Словарь с данными по конкретному филду.
        :rtype: dict

        """
        raise NotImplementedError


class StandardParser(BaseParser):
    """
    Стандартный парсер сериалайзеров.

    """
    def get_serializer_fields(self, serializer=None, exclude_fields=None, *args, **kwargs):
        """
        Возвращает список фидлов у сериалайзера.

        :param rest_framework.serializers.Serializer serializer: Класс сериалайзера, который парсим.
        :param iter exclude_fields: Поля, которые необходимо исключить из сериалайзера.

        :return: Список филдов сериалайзера.
        :rtype: iter

        """
        fields = []
        serializer = serializer or self.serializer_class
        if not serializer:
            return []

        # На сто процентов убеждаемся, что пришел проинициализированный сериалайзер.
        if not isinstance(serializer, serializers.BaseSerializer):
            serializer = serializer()

        extra_fields = getattr(getattr(serializer, 'Meta', {}), DefaultSettings.DOCS.SERIALIZER_DOC_ATTR, {})

        if isinstance(serializer, serializers.ListSerializer):
            # Обрабатываем список
            fields.append(
                self.get_field_props(
                    serializer,
                    sub_fields=self.get_serializer_sub_fields(serializer)
                )
            )

        if hasattr(serializer, 'get_fields'):
            for key, field in serializer.get_fields().items():
                if exclude_fields and key in exclude_fields:
                    continue

                label = None

                if extra_fields and isinstance(field, serializers.SerializerMethodField):
                    # Пробуем достать из мета класса.
                    ser = extra_fields.get(key, None)
                    if ser:
                        label = field.label
                        field = ser()

                to_many_relation = True if hasattr(field, 'many') else False
                sub_fields = self.get_serializer_sub_fields(field)
                choices_fields = None

                if isinstance(field, serializers.ChoiceField):
                    choices_fields = field.choices

                fields.append(
                    self.get_field_props(
                        field, key=key, sub_fields=sub_fields,
                        to_many_relation=to_many_relation, label=label,
                        choices_fields=choices_fields
                    )
                )

        return fields

    def get_serializer_sub_fields(self, field, *args, **kwargs):
        """
        Достает вложенные филды у филда.

        :param rest_framework.fields.Field rest_framework.serializers.Serializer field: Объект филда.

        :return: Список со вложенными филдами.
        :rtype: iter

        """
        sub_fields = None
        if isinstance(field, serializers.BaseSerializer):
            if hasattr(field, 'many'):
                if isinstance(field.child, serializers.BaseSerializer):
                    sub_fields = self.get_serializer_fields(field.child)
                elif isinstance(field, serializers.ListSerializer):
                    sub_fields = [self.get_field_props(field.child, key='[list-item]')]
            else:
                sub_fields = self.get_serializer_fields(field)
        return sub_fields

    def get_field_props(self, field, key=None, sub_fields=None,
                        to_many_relation=None, label=None, choices_fields=None, *args, **kwargs):
        """
        Формирует данные по конкретному филду.

        :param rest_framework.fields.Field rest_framework.serializers.Serializer field: Объект филда.
        :param str key: Название филда.
        :param list sub_fields: Вложенные филды, если это составной филд.
        :param bool to_many_relation: Указатель на Relation связи.
        :param str label: Текст описания филда label поле.
        :param tuple choices_fields: Значения, которые может принимать это поле.

        :return: Словарь с данными по конкретному филду.
        :rtype: dict

        """
        return {
            # Если нет field_name [предположительно] это корневой список без имени.
            'name': key if key is not None else (field.field_name if field.field_name else '[list]'),
            'type': str(field.__class__.__name__),
            'sub_fields': sub_fields,
            'required': field.required,
            'to_many_relation': to_many_relation if to_many_relation is not None else hasattr(field, 'many'),
            'label': label if label else field.label if field.label else '',
            'description': field.help_text if field.help_text else '',
            'choices_fields': choices_fields
        }


DefaultParser = StandardParser
