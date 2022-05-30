import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from telegram import TelegramError

from exceptions import (HomeworkExceptionError, RequestError, StatusCodeError,
                        TokenError)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = os.getenv('RETRY_TIME')
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(time)s'
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))


def send_message(bot, message):
    """Отправка сообщений о статусе домашней работы."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение отправлено: {message}')
    except Exception as error:
        logger.error(f'Ошибка при отправке сообщения: {error}')
        raise TelegramError(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    """Получение ответа от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            logger.error(f'Сбой в работе программы: Эндпоинт {ENDPOINT} '
                         f'недоступен. Код ответа API: {response.status_code}')
            raise StatusCodeError('Код ответа сервера. '
                                  f'{response.status_code}')
        return response.json()
    except RequestError as request_error:
        logger.error(f'Код ответа API: {request_error}')
        raise RequestError(f'Код ответа API: {request_error}')
    except ValueError:
        logger.error('JSON некорректен')
        raise ValueError('JSON некорректен')


def check_response(response):
    """Проверка запроса."""
    try:
        homework = response['homeworks']
    except KeyError:
        logger.error('Неверный ключ')
        raise KeyError('Неверный ключ')
    if not isinstance(homework, list):
        logger.error('Ошибка в данных')
        raise HomeworkExceptionError('Ошибка в данных')
    return homework


def parse_status(homework):
    """Проверка статуса домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        raise KeyError('homework_name отсутствует')
    if homework_status is None:
        raise KeyError('homework_status отсутствует')
    if homework_status not in HOMEWORK_STATUSES.keys():
        raise KeyError('Некорректный статус домашней работы')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствуют необходимые переменные окружения')
        raise TokenError('Отсутствуют необходимые переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            check_homework = check_response(response)
            if check_homework != check_homework[0]:
                message = parse_status(check_homework)
                send_message(bot, message)
            else:
                logger.debug('Обновлений по статусу ревью нет.')
                current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Ошибка отправки сообщения: {error}'
            logger.error(message)
            response = send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
