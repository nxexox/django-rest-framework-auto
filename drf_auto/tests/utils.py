"""
Хэлперы для автотестов.

"""


def test_helper_factory(field_class=None, value=None, as_dict=None):
    """
    Создает дочерний класс от `field_class` с дополнительными аттрибутами (с префиксом test_helper_) для тестирования.
    Можно использовать как декоратор для класса.

    :param any field_class: Любой класс.
    :param any value: Значение для теста.
    :param bool as_dict: Описывает ли сериалайзер один объект из словаря.

    :return: Новый класс.

    """
    def decor(field_class):
        attrs = {}

        if value is not None:
            attrs['test_helper_value'] = value

        if as_dict is not None:
            attrs['test_helper_as_dict'] = True

        return type(field_class.__name__, (field_class,), attrs)

    if field_class is None:
        return decor
    else:
        return decor(field_class)


class Deferred(object):
    """
    Экземпляр этого класса в автотестах заменяется на pk экземпляра модели `model`.

    """
    model = None
    force_create = False

    def __init__(self, model, force_create=False):
        """
        :param any model: Класс модели.
        :param bool force_create: Не получать имеющийся объект, а создавать новый.

        """
        self.model = model
        self.force_create = force_create
