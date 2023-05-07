import sys
import os
import time
import json
import redis
import sherlock
from threading import Thread
from datetime import datetime as dt

def now_time():
    return dt.now().strftime("%d/%m/%Y %H:%M:%S")
r = redis.StrictRedis(host='redis', port=6379, decode_responses=True)

def sherlock_start(request):
    filename = f'/opt/sherlock/results/{request["payload"]}.txt'
    sys.argv[1] = f'--output'
    sys.argv[2] = filename
    sys.argv[3] = request["payload"]
    sherlock.main()
    raw_response = open(filename, 'r').read()
    response = raw_response.split('\n')
    request['response'] = response[:-2]
    unsver = json.dumps(request, ensure_ascii=False)
    r.lpush('response', f'{unsver}')
    os.remove(filename)

def get_responce():
    while True:
        data_list = r.lrange('sherlock', 0, -1)
        if len(data_list) > 0:
            for id_nick in range(len(data_list)):
                request = json.loads(data_list[id_nick].replace("\'", '\"'))
                response = Thread(target=sherlock_start, args=(request,))
                response.start()
                r.lrem('sherlock', 1, f'{data_list[id_nick]}')
        else:
            time.sleep(30)

if __name__ == "__main__":
    get_responce()
