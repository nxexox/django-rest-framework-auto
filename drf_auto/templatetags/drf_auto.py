from django import template
from django.template.defaultfilters import stringfilter

from rest_framework.utils.formatting import markup_description

from ..settings import DefaultSettings

register = template.Library()


information = 'Любая точка может вернуть ошибку с кодом. </br>' \
              'В таком случае, код ответа сервера будет нести информационный характер, ' \
              'какого рода ошибка. Так же дополнительно передается два параметра: <b>code</b> и <b>message</b>. </br>' \
              'В <b>code</b> находится код ошибки, который содержит полную информацию по ошибке, ' \
              'а <b>message</b> расшифровка этого кода.</br>'

# Добавляем общю инфу по кодам.
information += 'Типы кодов:</br><ul class="fields list">{}</ul>'.format(
    ''.join((
        '<li class="fields">{key} - {val}</li>'.format(key=key, val=val)
        for key, val in DefaultSettings.CODES.get('common', []).items()
    ))
)

# Добавляем простую информацию.
information += 'Коды:</br><ul class="fields list">{}</ul>'.format(
    ''.join((
        '<li class="fields">{key} - {val}</li>'.format(key=key, val=val)
        for key, val in DefaultSettings.CODES.get('specific', []).items()
    ))
)


@register.filter(name='markdown')
@stringfilter
def markdown(value):
    return markup_description(value)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.simple_tag
def get_settings_formats():
    return {
        '<id>': 'Некий параметр, который передается как часть URL.',
        'Ошибки': information
    }
