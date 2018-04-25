"""
Ошибки для автоапи Rest API.

"""


class FailPointRequest(Exception):
    """
    Ошибка, которая срабатывает, когда во время обработки апи произошла ошибка.

    """
    def __init__(self, status, code=None, message=None, data=None, fields=None, *args, **kwargs):
        """
        Ошибка, во время обработки запроса. Аналогична методу fail у автореста.

        :param int status: Код ответа от сервера.
        :param int code: Код, который вернется в параметре `code`. По дефолту `code` = `status`.
        :param str message: Сообщение, которое переопределит стандартное для `code`. По дефолту стандартное сообщение.
        :param dict data: Доп данные которые вернуться в запросе. Добавляются только если указаны или есть в fields.
        :param dict fields: Словарь филдов, для управления ответов.
                            Ключ это ключ который вернется, значение, это ключ из стандартного набора атрибутов.
                            Приммер: {'response_code': 'code', 'response_message': 'message'}
                            В таком случае ответ всегда будет фиксирован и выглядеть так:
                            {'response_code': code, 'response_message': message}. Вне зависимости от доп данных.
        :param iter args: Позиционные аргументы для базового Exception.
        :param dict kwargs: Именованные аргументы для базого Exception.

        """
        super().__init__(*args, **kwargs)
        self.status = status
        self.code = code
        self.message = message
        self.data = data
        self.fields = fields
