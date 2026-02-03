import requests
import time
import logging
import telegram
from environs import Env


logger = logging.getLogger(__name__)


def parse_lesson_statuses(checklist):
    lessons = []

    for attempt in checklist['new_attempts']:
        lesson = {
            'lesson_title': attempt['lesson_title'],
            'lesson_url': attempt['lesson_url'],
            'status_message': (
                "❌ К сожалению, в работе нашлись ошибки."
                if attempt['is_negative']
                else "✅ Преподавателю все понравилось, можно приступать к следующему уроку!"
            )
        }
        lessons.append(lesson)

    return lessons


def send_telegram_messages(bot, tg_chat_id, lessons):
    for lesson in lessons:
        bot.send_message(
            chat_id=tg_chat_id,
            text=(
                "У вас проверили работу «Отправляем уведомления о проверке работ»\n\n"
                f"Название урока - «{lesson['lesson_title']}»\n\n"
                f"«{lesson['status_message']}»\n\n"
                f"Ссылка на урок - «{lesson['lesson_url']}»"
            )
        )


def get_checklist_from_api(dvmn_api_token, timestamp=None):
    """Делает запрос к API DVMN и возвращает JSON."""
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {dvmn_api_token}'
    }
    payload = {'timestamp': timestamp} if timestamp is not None else None
    response = requests.get(url, headers=headers, timeout=90, params=payload)
    response.raise_for_status()
    return response.json()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )

    env = Env()
    env.read_env()

    dvmn_api_token = env.str('DVMN_TOKEN')
    tg_bot_token = env.str('TELEGRAM_BOT_TOKEN')
    tg_chat_id = env.str('TELEGRAM_CHAT_ID')
    bot = telegram.Bot(token=tg_bot_token)

    timestamp = None
    logger.info('Запуск long polling')

    while True:
        try:
            checklist = get_checklist_from_api(dvmn_api_token, timestamp)

            if checklist['status'] == 'found':
                timestamp = checklist['last_attempt_timestamp']
                logger.info("Найдены проверки, обновили timestamp")
                lessons = parse_lesson_statuses(checklist)
                send_telegram_messages(bot, tg_chat_id, lessons)

            elif checklist['status'] == 'timeout':
                timestamp = checklist['timestamp_to_request']
                logger.debug("Обновлений нет, получили новый timestamp")

        except requests.exceptions.ReadTimeout:
            logger.debug("ReadTimeout — сервер не прислал обновлений")
            continue

        except requests.exceptions.ConnectionError:
            logger.warning("Нет интернета, повтор через 5 секунд")
            time.sleep(5)
            continue

        except Exception as e:
            logger.exception(f"Неожиданная ошибка: {e}")
            time.sleep(5)
            continue


if __name__ == "__main__":
    main()
