import os
import re
import time
import json
import base64
import redis
from datetime import datetime
from asgiref.sync import async_to_sync, sync_to_async
from seleniumwire import webdriver
from selenium.webdriver.common.by import By

r = redis.StrictRedis(host='redis', port=6379, decode_responses=True)
gmailId = os.environ.get('GMAILID')
passWord = os.environ.get('PASSWORD')
ipServ = os.environ.get('IPSERVER')

selinoid_options = {
    "browserName": "chrome",
    "browserVersion": "96.0.4664.45",
    "acceptSslCerts": True,
    "sessionTimeout": '90h',
    "selenoid:options": {
        "enableVNC": True,
        "enableVideo": False,
        "enableLog": True,
        "sessionTimeout": '90h'
    }
}

seleniumwire_options = {
    'suppress_connection_errors': False,
    'auto_config': False,
    'enable_har': True,
    'addr': '0.0.0.0',
    'port': 8087,
}

options_capability = webdriver.ChromeOptions()
options_capability.set_capability("browserVersion", "96.0.4664.45")
options_capability.set_capability("selenoid:options", selinoid_options)
ch_opt = {"args": ["test-type", "disable-infobars", "--disable-gpu", "no-sandbox", "disable-setuid-sandbox",
                   "start-fullscreen"], "w3c": False}
options_capability.set_capability('goog:chromeOptions', ch_opt)
options_capability.add_argument('--ignore-certificate-errors')
options_capability.add_argument(f'--proxy-server={ipServ}:8087')
already_waiter_time = 0

def waite(driver, nextButton, wait_time=0):
    if wait_time < 120:
        time.sleep(10)
        wait_time += 1
        get_capcha_text(driver, nextButton, wait_time)
    else:
        driver.close()
        driver.quit()
        r.delete('ghunt_cookies_capcha')
        r.set('COOKIES', "False")
        responses = r.lrange('response', 0, -1)
        for resp in responses:
            if resp.find('Bad cookies') > 0:
                r.lrem('response', 1, resp)
        exit('Time over')

def get_capcha_text(driver, nextButton, wait_time=0):
    if os.environ.get('CAPCHA_TEXT') == None:
        waite(driver, nextButton, wait_time)
    else:
        driver.find_element(By.XPATH, '//*[@id="ca"]').send_keys(os.environ.get('CAPCHA_TEXT'))
        nextButton.click()
        del os.environ['CAPCHA_TEXT']
        time.sleep(5)
        capcha_validate(driver, nextButton)


def save_page(driver, name):
    with open(f'/connectservice/tmp/{name}.txt', 'w') as r:
        r.write(f"{driver.page_source}")


def capcha_validate(driver, nextButton):
    srcs = driver.find_element(By.ID, 'captchaimg').get_attribute('src')
    if srcs != None:
        msg = {
            "types": "capcha",
            "payload": srcs,
        }

        r.set('ghunt_cookies_capcha', json.dumps(msg))
        for ws in connected_user:
            try:
                async_to_sync(ws.send)(json.dumps(msg))
            except:
                ...
        get_capcha_text(driver, nextButton)


def get_gcokies():
    r.set('ghunt_cookies_stop', "True")
    try:
        driver = webdriver.Remote(command_executor=f"http://{ipServ}:4444/wd/hub",
                                  seleniumwire_options=seleniumwire_options,
                                  options=options_capability)
    except Exception as exp:
        print(f'Exception {exp}')
    driver.implicitly_wait(25)
    driver.get(
        "http://accounts.google.com/signin/v2/identifier?continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&service=mail&sacu=1&rip=1&flowName=GlifWebSignIn&flowEntry=ServiceLogin")
    time.sleep(1)
    driver.save_screenshot('/connectservice/tmp/open.png')
    driver.find_element(By.XPATH, '//*[@id ="identifierId"]').send_keys(gmailId)
    time.sleep(1)
    nextButton = driver.find_element(By.XPATH, '//*[@id="identifierNext"]/div/button')
    nextButton.click()
    time.sleep(3)
    driver.save_screenshot('/connectservice/tmp/login.png')
    capcha_validate(driver, nextButton)
    r.set('COOKIES', "False")
    driver.save_screenshot('/connectservice/tmp/capcha_valid.png')
    driver.find_element(By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input').send_keys(passWord)
    r.delete('ghunt_cookies_capcha')
    time.sleep(1)
    driver.find_element(By.XPATH, '//*[@id ="passwordNext"]').click()
    time.sleep(6)
    driver.save_screenshot('/connectservice/tmp/connect_ok.png')
    print(f'{datetime.now().strftime("%Y/%m/%d %H:%M:%S")} [{os.getpid()}] [Get Cookies] Login was Ok Starting collect cookies')
    user_cookies = {}
    lSID = str
    for request in driver.requests:

        try:
            XLSID = re.findall(r'set-cookie: LSID.+;Path', str(request.response.headers))
            if XLSID:
                lSID = XLSID[0].replace('set-cookie: LSID=', '').replace(';Path', '')
                break
        except:
            pass
    LLSID = 'o.chat.google.com|o.mail.google.com|s.UA|s.youtube:' + lSID,
    user_cookies["LSID"] = LLSID[0]
    try:
        for i in driver.get_cookies():
            if 'SID' == i["name"]:
                user_cookies["SID"] = i["value"]
            elif '__Secure-3PSID' in i["name"]:
                user_cookies["__Secure-3PSID"] = i["value"]
            elif 'LSID' == i["name"]:
                user_cookies["LSID"] = i["value"]
            elif 'HSID' == i["name"]:
                user_cookies["HSID"] = i["value"]
            elif 'SSID' == i["name"]:
                user_cookies["SSID"] = i["value"]
            elif 'APISID' == i["name"]:
                user_cookies["APISID"] = i["value"]
            elif 'SAPISID' == i["name"]:
                user_cookies["SAPISID"] = i["value"]
        json_string = json.dumps(user_cookies)
        with open('/connectservice/tmp/111.txt', 'w', encoding='utf-8') as f:
            f.write(json_string)
        message_bytes = json_string.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')
        print(f'\n{datetime.now().strftime("%Y/%m/%d %H:%M:%S")} [{os.getpid()}] [Get Cookies] Cookies is: {base64_message}\n')
        return base64_message
    except:
        pass

    finally:
        driver.quit()


async def start_get_cookies(connected):
    global connected_user
    connected_user = connected
    coockies = await sync_to_async(get_gcokies)()
    return coockies

if __name__ == '__main__':
    get_gcokies()