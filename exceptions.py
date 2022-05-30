class StatusCodeError(Exception):
    """Некорректный статус ответа сервера."""
    pass


class RequestError(Exception):
    """Некорректный запрос."""
    pass


class HomeworkExceptionError(Exception):
    """Ошибка в данных по ключу homework."""
    pass


class TokenError(Exception):
    """Отсутствуют необходимые переменные окружения."""
    pass
