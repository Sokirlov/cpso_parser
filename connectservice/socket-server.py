import os
import re
import json
import asyncio
import websockets
import redis
from datetime import datetime as dt
from get_cookies import start_get_cookies

def now_time():
    return dt.now().strftime("%Y/%m/%d %H:%M:%S")


r = redis.StrictRedis(host='redis', port=6379, decode_responses=True)
in_work = []
SOKEY = os.environ.get('SOKEY')
CLIENTS = set()

async def get_responce(connected):
    z =True
    while z==True:
        response_list = r.lrange('response', 0, 1)
        if len(response_list) > 0:
            dp = response_list[0].replace("\'", "\"").replace("\'", "\"")
            try:
                dpp = dp.decode(encoding='utf-8')
            except:
                dpp = dp
            try:
                respond = json.loads(dp.replace("\'", "\""))
            except:
                prew_data =re.match(r'^.+\"response\"', dp.replace("\'", "\""))[0].replace(', "response"', '}')
                respond = json.loads(prew_data.replace("\'", "\""))
                respond['response'] = 'Json response is not valid'
                respond['types'] = 'error'
            finally:
                if respond['response'] == 'Bad cookies':
                    z = False
                    try:
                        if r.get('ghunt_cookies_stop') == "False":
                            cookies = await start_get_cookies(connected)
                            msg = {"types": "update_cookies", "payload": f"{cookies}", "social": "ghunt"}
                            r.lpush("ghunt", f"{msg}")
                        else:
                            continue
                        z = True
                        await asyncio.sleep(200)
                    except:
                        exit()
                else:
                    respond_json = json.dumps(respond, ensure_ascii=False)
                    for ws in connected:
                        await ws.send(respond_json)
                    r.lrem('response', 1, response_list[0])
        else:
            await asyncio.sleep(2)
            pass


async def pushing_msg(message_str, connected):
    message = json.loads(message_str)
    if message['types'] == 'capcha':
        os.environ['CAPCHA_TEXT'] = message['payload']
    else:
        if message['social'] == 'ghunt':
            r.set('ghunt_cookies_stop', 'False')
            if r.get('COOKIES') == "True":
                cookies_msg = r.get('ghunt_cookies_capcha')
                for ws in connected:
                    await ws.send(f"{cookies_msg}")
        query = r.lrange(message['social'], 0, -1)
        if f'{message}' in query:
            resp = message
            resp['types'] = 'in_query'
            respons = json.dumps(resp, ensure_ascii=False)
            for ws in connected:
                await ws.send(respons)
        else:
            r.rpush(f"{message['social']}", f"{message}")
            resp = message
            resp['types'] = 'in_query'
            respons = json.dumps(resp, ensure_ascii=False)
            for ws in connected:
                await ws.send(respons)

async def parsed(websocket):
    try:
        secure = websocket.request_headers["secure"]
    except:
        secure = None
    if secure == SOKEY:
        try:
            CLIENTS.add(websocket)
            response = asyncio.create_task(get_responce(CLIENTS))
            async for message_str in websocket:
                msg_push = asyncio.create_task(pushing_msg(message_str, CLIENTS))
                await msg_push
            await response
            CLIENTS.remove(websocket)
        except:
            CLIENTS.remove(websocket)
    else:
        await websocket.send('BYE-BYE !')

async def main():
    async with websockets.serve(parsed, host="0.0.0.0", port=8765):
        await asyncio.Future()

if __name__ == "__main__":
    r.set('COOKIES', "False")
    asyncio.run(main())