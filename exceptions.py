class StatusCodeError(Exception):
    """Некорректный статус ответа сервера."""

    pass


class RequestError(Exception):
    """Некорректный запрос."""

    pass


class ResponseAnswerStatusError(Exception):
    """Ошибка в статусе ответа."""

    pass


class HomeworkExceptionError(Exception):
    """Ошибка в данных по ключу homework"""

    pass