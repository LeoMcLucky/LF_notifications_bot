import requests
from environs import Env
import time
from pprint import pprint
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


def req(token):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {token}'
    }

    timestamp = None
    logger.info('Запуск long polling')

    while True:
        payload = {'timestamp': timestamp} if timestamp is not None else None

        try:
            logger.debug('Отправляем запрос, timestamp=%s', timestamp)

            response = requests.get(
                url,
                headers=headers,
                timeout=5,
                params=payload,
            )
            response.raise_for_status()

            checklist = response.json()
            pprint(checklist)

        except requests.exceptions.ReadTimeout:
            logger.debug('ReadTimeout — сервер не прислал обновлений')
            continue

        except requests.exceptions.ConnectionError:
            logger.warning('Нет интернета, повтор через 5 секунд')
            time.sleep(5)
            continue

        except Exception:
            logger.exception('Неожиданная ошибка')
            time.sleep(5)
            continue

        if checklist['status'] == 'found':
            timestamp = checklist['last_attempt_timestamp']
            logger.info('Найдены проверки, обновили timestamp')

        elif checklist['status'] == 'timeout':
            timestamp = checklist['timestamp_to_request']
            logger.debug('Обновлений нет, получили новый timestamp')


def main():
    env = Env()
    env.read_env()

    dvmn_token = env.str('DVMN_TOKEN')
    req(dvmn_token)


if __name__ == "__main__":
    main()
