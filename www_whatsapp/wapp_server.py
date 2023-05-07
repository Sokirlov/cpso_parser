import os
import json
import time
import redis
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime as dt


def now_time():
    return dt.now().strftime("%d/%m/%Y %H:%M:%S")
r = redis.StrictRedis(host='redis', port=6379, decode_responses=True)
IPServ = os.environ.get('IPSERVER')
DIR_TO_SAVE = "/wsserver/tmp/"

chrome_options = Options()
chrome_options.add_argument('start-maximized')
chrome_options.add_argument('disable-popup-blocking')
_SELENOID_OPTIONS = {
    "browserName": "chrome",
    "browserVersion": "96.0.4664.45",
    "acceptSslCerts": True,
    "sessionTimeout": "876000h",
    "selenoid:options": {
        "enableVNC": True,
        "enableVideo": False,
        "enableLog": True,
    }
}
_OPTIONS = webdriver.ChromeOptions()  # options for starting a webdriver in docker container
_OPTIONS.set_capability("browserVersion", "96.0.4664.45")
_OPTIONS.set_capability("selenoid:options", _SELENOID_OPTIONS)
_CH_OPT = {"args": ["disable-infobars", "--disable-gpu"], "w3c": False}
_OPTIONS.set_capability('goog:chromeOptions', _CH_OPT)
_OPTIONS.add_argument("start-maximized")

class WhatsappWeb():
    def validate_phone(self, request):
        original_window = self.driver.current_window_handle
        self.driver.switch_to.new_window('tab')
        self.driver.save_screenshot(f'{DIR_TO_SAVE}new_tab.png')
        self.get_main_page()
        time.sleep(2)
        self.driver.save_screenshot(f'{DIR_TO_SAVE}before_phone.png')
        self.driver.get(f'https://web.whatsapp.com/send?phone={request["payload"]}')
        time.sleep(5)
        try:
            main_fraim = self.driver.find_element(By.ID, 'main')
            main_fraim.find_element(By.CSS_SELECTOR, '[role="button"]').click()
            time.sleep(1)
            try:
                avatar = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="drawer-right"]').find_element(By.TAG_NAME, 'img').get_attribute('src')
            except:
                avatar = None
            if avatar:
                response = {'whatsapp': True, 'avatar': avatar}
            else:
                response = {'whatsapp': True, 'avatar': False}
        except:
            response = {'whatsapp': False}
        finally:
            request['response'] = response
            answer = json.dumps(request, ensure_ascii=False)
            r.lpush('response', answer)
            self.driver.close()
            self.driver.switch_to.window(original_window)

    def qr_walidation(self):
        qr_old = None
        while True:
            try:
                qr_new = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="qrcode"]')
            except:
                qr_new = None

            if qr_new:
                if qr_new.get_attribute("data-ref") != qr_old:
                    qr_new.screenshot(f'{DIR_TO_SAVE}whatsapp_qr_new.png')
                    with open(f'{DIR_TO_SAVE}whatsapp_qr_new.png', 'rb') as file:
                        img_qr = base64.b64encode(file.read())
                        answer = dict(types='qr', social="whatsapp", response=img_qr.decode('utf-8'))
                        response = json.dumps(answer, ensure_ascii=False)
                        r.lpush('response', response)
                        qr_old = qr_new.get_attribute("data-ref")
                else:
                    time.sleep(2)
            else:
                break

    def get_main_page(self):
        self.driver.get("https://web.whatsapp.com/")
        self.driver.implicitly_wait(5)
        time.sleep(1)
        self.qr_walidation()

    def __init__(self):
        self.driver = webdriver.Remote(command_executor=f"http://{IPServ}:4444/wd/hub", options=_OPTIONS)
        self.get_main_page()
        print(f"{now_time()} [-] [WhatsApp] service is starting")
        os.remove(f'{DIR_TO_SAVE}whatsapp_qr_new.png')
        self.driver.save_screenshot(f'{DIR_TO_SAVE}2.png')

def sessionOpener():
    ww = WhatsappWeb()
    while True:
        data_list = r.lrange('whatsapp', 0, -1)
        if len(data_list) > 0:
            for req in range(len(data_list)):
                request = json.loads(data_list[req].replace("\'", '\"'))
                ww.validate_phone(request)
                r.lrem('whatsapp', 1, f'{data_list[req]}')
        else:
            time.sleep(10)

if __name__ == "__main__":
    sessionOpener()
