#!/usr/bin/env python3
import subprocess
import os
import sys
import asyncio
from datetime import datetime as dt
sys.path.insert(-1, '/usr/src/app/ghunt')
from pathlib import Path
from lib.utils import *
from modules.email import email_hunt
import redis

now_time = dt.now().strftime("%Y/%m/%d %H:%M:%S")
r = redis.StrictRedis(host='redis', port=6379, decode_responses=True)



async def waite(tt=0):
    while True:
        if cook := r.get('COOKIES') == "True":
            tt += 30
            print(f'{now_time} [-] [GHunt] чекаэмо {tt} секунд {cook}')
            await asyncio.sleep(30)
        else:
            tt = 0
            break



async def get_responce():
    while True:
        data_list = r.lrange('ghunt', 0, 1)
        if len(data_list) > 0:
            request = json.loads(data_list[0].replace("\'", '\"'))
            if request['types'] == 'update_cookies':
                print(f'{now_time} [-] [GHunt] Start generate New cookies & keys with {request["payload"]}')
                os.chdir(Path(__file__).parents[0])
                subprocess.run(["python3", "check_and_gen.py"], input=f"2\n{request['payload']}\n", encoding='utf-8')
                r.lrem('ghunt', 1, f'{request}')
            else:
                try:

                    if r.get('ghunt_cookies_stop') == 'True':
                        await asyncio.sleep(30)
                    else:
                        response = email_hunt(request['payload'])
                        response = json.loads(response.replace("\'", '\"'))
                        r.lrem('ghunt', 1, f'{request}')
                        request['response'] = response
                        unswer = json.dumps(request)
                        r.lpush('response', f'{unswer}')
                except Exception as err:
                    if str(err) == 'Bad cookies':
                        r.set('COOKIES', "True")
                        if os.path.exists('/usr/src/app/resources/save.txt'):
                            os.remove('/usr/src/app/resources/save.txt')
                        request["types"] = 'error'
                        request["response"] = f'{err}'
                        r.lpush('response', f'{request}')
                        await waite()
                    else:
                        r.lrem('ghunt', 1, f'{request}')
                    request["types"] = 'error'
                    request["response"] = f'{err}'
                    r.lpush('response', f'{request}')
        else:
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(get_responce())

