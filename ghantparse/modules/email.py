#!/usr/bin/env python3

import json, sys, os, subprocess
from types import SimpleNamespace
from datetime import datetime
from io import BytesIO
from os.path import isfile
from pathlib import Path
from pprint import pprint

import httpx
from PIL import Image
from geopy.geocoders import Nominatim

import config, socket
import lib.gmaps as gmaps
import lib.youtube as ytb
from lib.photos import gpics
from lib.utils import *
import lib.calendar as gcalendar


now_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def wr_log(data, name):
    with open(f'/gtmp/{name}.txt', 'w', encoding='UTF-8') as wrt:
        wrt.write(f'{data}')

main_data = {}
# profile_pic_flathash = []

def make_main_dict(**kwargs):
    # print('start make_main_dict')
    for name, val in kwargs.items():
        main_data[name] = val
    print('ready to write data')
    wr_log(main_data, 'main_data')
    print('Write is ok')

def main_data_validate(data):
    # print(f"Data {data['matches'][0]}")
    # global valid_data
    # valid_data = {}
    # print('start main_data_validate')
    try:
        main_data['lookupId'] = data["matches"][0]["lookupId"]
    except KeyError:
        main_data['lookupId'] = None
    # print('Is ok  lookupId')
    try:
        main_data['gaiaID'] = data["matches"][0]["personId"][0]
        perid = main_data['gaiaID']
    except KeyError:
        main_data['gaiaID'] = ''
        perid = ''

    # print(f'Is ok  gaiaID {perid}')
    people = data['people'][perid]
    try:
        main_data['lastUpdated'] = people['metadata']['identityInfo']['sourceIds'][0]['lastUpdated']
    except KeyError:
        main_data['lastUpdated'] = ''
    # print(f"Is ok  lastUpdated {main_data['lastUpdated']}")

    try:
        url = people['photo'][0]['url']
    except KeyError:
        url = ''

    try:
        photoToken = people['photo'][0]['photoToken']
    except KeyError:
        photoToken = ''

    # print(f"Try {url} \n 22 {photoToken}")
    main_data['photo'] = dict(url=url, photoToken=photoToken)
    # print('Is ok  photo')

    try:
        main_data['fingerprint'] = people['fingerprint']
    except KeyError:
        main_data['fingerprint'] = None
    # print('Is ok  fingerprint')
    inAppReachability = []
    try:
        for i in people['inAppReachability']:
            inAppReachability.append(i['appType'])
    except KeyError:
        inAppReachability = []
    main_data['inAppReachability'] = [x.capitalize() for x in inAppReachability]
    # print('Is ok  inAppReachability')
    try:
        timestamp = int(people["metadata"]["lastUpdateTimeMicros"][:-3])
        last_edit = datetime.utcfromtimestamp(timestamp).strftime("%Y/%m/%d %H:%M:%S")  # (UTC)")
        main_data["last_edit"] = last_edit
    except KeyError:
        main_data["last_edit"] = ''
    try:
        main_data['isBot'] = people['extendedData']['hangoutsExtendedData']['isBot']
    except KeyError:
        main_data['isBot'] = False

    # print('main_data_validate collected')


def account_validate(account, client):
    # print('account_validate start')
    try:
        main_data['name'] = account["name"]
    except KeyError:
        main_data['name'] = ''
    try:
        main_data['organizations'] = account["organizations"]
    except KeyError:
        main_data['organizations'] = ''
    try:
        main_data['locations'] = account["locations"]
    except KeyError:
        main_data['locations'] = ''
    try:
        main_data['profile_pics'] = account["profile_pics"][0].url
        profile_pic_url = main_data['profile_pics']
        req = client.get(profile_pic_url)
        profile_pic_img = Image.open(BytesIO(req.content))
        global profile_pic_flathash
        profile_pic_flathash = image_hash(profile_pic_img)
    except KeyError:
        main_data['profile_pics'] = ''
    try:
        main_data['cover_pics'] = account['cover_pics'][0].url
    except KeyError:
        main_data['cover_pics'] = ''

    # print('account_validate finish')
# make_main_dict(**valid_data)

def youtube_validate(data, name):
    # print('Start validate YouTube')
    # print(f'Flat hash is {profile_pic_flathash}')
    confidence = None
    if not data:
        main_data["YouTubeChannel"] = "YouTube channel not found."
    else:
        confidence, channels = ytb.get_confidence(data, name, profile_pic_flathash)
        if confidence:
            ytb_dta = {}
            for channel in channels:
                ytb_dta[channel['name']] = channel['profile_url']
            main_data["YouTubeChannel"] = ytb_dta
            possible_usernames = ytb.extract_usernames(channels)
            if possible_usernames:
                posusname = []
                for username in possible_usernames:
                    posusname.append(username)
                main_data["PossibleUsernames"] = posusname
        else:
            main_data["YouTubeChannel"] = ""
    # print('Stop validate YouTube')



def gmaps_validate(reviews):
    # print('Start pars GMaps')
    geolocator = Nominatim(user_agent="nominatim")
    if reviews:
        confidence, locations = gmaps.get_confidence(geolocator, reviews, config.gmaps_radius)
        main_data["ProbableLocation"] = confidence
        loc_variants = []
        loc_names = []
        for loc in locations:
            loc_names.append(
                f"- {loc['avg']['town']}, {loc['avg']['country']}"
            )
            x = loc['avg']
            loc_variants.append(f'{x}')
        loc_names = set(loc_names)  # delete duplicates
        # main_data["loccation"] = str(loc_variants[0])
        main_data["loccation"] = list(loc_names)

    wr_log(main_data, 'main_data')
    # print('Finish parse GMaps')

def email_hunt(email):
    print(f"{now_time} [-] [GHunt e-mail] start {email}")
    if not email:
        raise Exception("Please give a valid email.\nExample : larry@gmail.com")

    if not isfile(config.data_path):
        # get_new_cookies()
        raise Exception("Bad cookies")

    hangouts_auth = ""
    hangouts_token = ""
    internal_auth = ""
    internal_token = ""
    cookies = {}

    with open(config.data_path, 'r') as f:
        out = json.loads(f.read())
        hangouts_auth = out["hangouts_auth"]
        hangouts_token = out["keys"]["hangouts"]
        internal_auth = out["internal_auth"]
        internal_token = out["keys"]["internal"]
        cookies = out["cookies"]

    print('Cockies is OK')
    client = httpx.Client(cookies=cookies, headers=config.headers)

    data = is_email_google_account(client, hangouts_auth, cookies, email, hangouts_token)

    # print('is_email_google_account', type(data), data)
    if type(data) == str:
        print(f'data problem {data}')
        raise Exception(data)

        # return {'error': data}
    # except:
    #     print('is_email_google_account', type(data), data)
    #     if data == str:
    #         print('Its work')
    #     return data

    main_data_validate(data)


    # print('Make a log with is_email_google_account')
    # wr_log(data, 'is_email_google_account')
    #
    # is_within_docker = within_docker()
    # if is_within_docker:
    #     print("[+] Docker detected, profile pictures will not be saved.")



    gaiaID = main_data['gaiaID']
    account = get_account_data(client, gaiaID, internal_auth, internal_token, config)
    account_validate(account, client)
    name = account["name"]
    if name:
        confidence = None
        ydata = ytb.get_channels(client, name, config.data_path, config.gdocs_public_doc)
        print('Make a log with ytb.get_channels')
        # wr_log(ydata, 'ytb.get_channels')
        youtube_validate(ydata, name)

    try:
        reviews = gmaps.scrape(gaiaID, client, cookies, config, config.headers, config.regexs["review_loc_by_id"],
                               config.headless)
    except:
        reviews = None

    calendar_response = gcalendar.fetch(email, client, config)
    if calendar_response:
        events = calendar_response["events"]
        if events:
            main_data["GoogleCalendar"] = gcalendar.out(events)
        else:
            main_data["GoogleCalendar"] = 'No events'
    else:
        main_data["GoogleCalendar"] = 'No public Google Calendar.'

    # print(f'Ready to send {parsed_data}')
    return json.dumps(main_data)