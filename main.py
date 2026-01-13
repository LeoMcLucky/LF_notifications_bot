import requests
from environs import Env
import time
from pprint import pprint


def req(token):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {token}'
    }
    timestamp = None
    print('timestamp2', timestamp)

    while True:
        payload = {'timestamp': timestamp} if timestamp is not None else None
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=90,
                params=payload,
            )
            response.raise_for_status()
            checklist = response.json()
            pprint(checklist)
            print('timestamp', timestamp)

        except requests.exceptions.ReadTimeout:
            print('Продолжаем')
            continue

        except requests.exceptions.ConnectionError:
            time.sleep(5)
            print('нет интернета')
            continue

        if checklist['status'] == 'found':
            timestamp = checklist['last_attempt_timestamp']

        elif checklist['status'] == 'timeout':
            timestamp = checklist['timestamp_to_request']


def main():
    env = Env()
    env.read_env()
    dvmn_token = env.str('DVMN_TOKEN')
    req(dvmn_token)


if __name__ == "__main__":
    main()
