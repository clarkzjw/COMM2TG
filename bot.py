# -*- coding: utf-8 -*-

import os
import re
import time
import json
import logging
import urllib
from selenium import webdriver

import telegram
from telegram.error import NetworkError
from pymongo import MongoClient

import ingrex

Debug = True
bot = None
BOT_TOKEN = ''
CHANNEL_NAME = ''
Email = ''
Passwd = ''
PhantomjsPath = ''
DBName = ''
DBUser = ''
DBPass = ''
DBHost = ''
BlockList = ''

LOG_FILENAME = 'voh.log'
logging.basicConfig(level=logging.DEBUG,
                    filename=LOG_FILENAME,
                    filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)


class CookieException(Exception):
    ''' CookieError '''


def getTime():
    return time.strftime('%x %X %Z')


def readConfig():
    global Email
    global Passwd
    global BOT_TOKEN
    global CHANNEL_NAME
    global PhantomjsPath
    global DBName
    global DBUser
    global DBPass
    global DBHost
    global BlockList

    configfile = open("./config.json")
    config = json.load(configfile)
    Email = config["Email"]
    Passwd = config["Passwd"]
    BOT_TOKEN = config["BOT_TOKEN"]
    CHANNEL_NAME = config["CHANNEL_NAME"]
    PhantomjsPath = config["PhantomjsPath"]
    DBName = config["DBName"]
    DBUser = config["DBUser"]
    DBPass = config["DBPass"]
    DBHost = config["DBHost"]
    BlockList = config["BlockList"]

    os.environ['TZ'] = 'Asia/Shanghai'
    time.tzset()


def fetchCookie():
    global Debug
    global Email
    global Passwd
    global PhantomjsPath

    logger = logging.getLogger('fetchCookie')
    logger.info(getTime() + ': Fetching Cookie...')

    driver = webdriver.PhantomJS(PhantomjsPath)
    driver.get('https://www.ingress.com/intel')

    # get login page
    link = driver.find_elements_by_tag_name('a')[0].get_attribute('href')
    driver.get(link)
    if Debug:
        driver.get_screenshot_as_file('1.png')
    # simulate manual login
    driver.set_page_load_timeout(10)
    driver.set_script_timeout(20)
    driver.find_element_by_id('Email').send_keys(Email)
    if Debug:
        driver.get_screenshot_as_file('2.png')
    driver.find_element_by_css_selector('#next').click()
    time.sleep(3)
    driver.find_element_by_id('Passwd').send_keys(Passwd)
    if Debug:
        driver.get_screenshot_as_file('3.png')
    driver.find_element_by_css_selector('#signIn').click()
    time.sleep(3)
    if Debug:
        driver.get_screenshot_as_file('3.png')
    # get cookies
    temp = driver.get_cookies()

    csrftoken = ''
    SACSID = ''
    for a in temp:
        if (a['name'] == 'csrftoken'):
            csrftoken = a['value']
        if (a['name'] == 'SACSID'):
            SACSID = a['value']

    if csrftoken == '' or SACSID == '':
        logger.error(getTime() + ': Fetch Cookie Failed')
        raise CookieException

    with open('cookie', 'w') as file:
        cookie = 'SACSID='+SACSID+'; csrftoken='+csrftoken+'; ingress.intelmap.shflt=viz; ingress.intelmap.lat=29.098418372855484; ingress.intelmap.lng=119.81689453125; ingress.intelmap.zoom=17'
        file.write(cookie)

    driver.quit()
    logger.info(getTime() + ': Fetching Cookie Succeed')
    return True


def sendMessge(bot, msg):
    "sendMsg"

    logger = logging.getLogger('sendMessage')
    while True:
        try:
            url = 'https://api.telegram.org/bot'
            url += BOT_TOKEN
            url += '/sendMessage?chat_id='
            url += CHANNEL_NAME
            url += '&text='
            url += urllib.parse.quote(msg)

            req = urllib.request.Request(url, headers={'Content-Type': 'application/x-www-form-urlencoded'})
            resp = urllib.request.urlopen(req)
            data = resp.read()
            logger.info(data)
            logger.info(getTime() + ": sendMsg " + msg)
            break
        except NetworkError:
            time.sleep(1)


def sendMonitor(bot, msg):
    logger = logging.getLogger('sendMonitor')
    while True:
        try:
            bot.sendMessage(chat_id="@voamonitor", text=msg)
            logger.info(getTime() + ": sendMsg " + msg)
            break
        except NetworkError:
            time.sleep(1)


def formatMessage(raw):
    pattern = re.compile(BlockList)
    match = pattern.search(str(raw))
    if match:
        return "Blocked"

    msg = ''
    plext = raw[2]['plext']
    markup = plext['markup']

    for mark in markup:
        if mark[0] == 'SECURE':
            msg += mark[1]['plain']
        elif mark[0] == 'SENDER':
            player = mark[1]['plain']
            team = mark[1]['team']

            pattern = re.compile(':')
            match = pattern.search(player)
            if match:
                if team == 'RESISTANCE':
                    player = player[:match.span()[0]] + ' 🐳' + player[match.span()[0]:]
                elif team == 'ENLIGHTENED':
                    player = player[:match.span()[0]] + ' 🐸' + player[match.span()[0]:]
            msg += player

        elif mark[0] == 'PLAYER' or mark[0] == 'AT_PLAYER':
            player = mark[1]['plain']
            team = mark[1]['team']

            msg += player
            if team == 'RESISTANCE':
                msg += ' 🐳'
            elif team == 'ENLIGHTENED':
                msg += ' 🐸'

        elif mark[0] == 'TEXT':
            msg += mark[1]['plain']

    pattern = re.compile('\[secure\]')
    match = pattern.search(msg)
    if match:
        if msg.find(':') != -1:
            msg = msg[:9] + '@' + msg[9:]
        else:
            msg = msg[:10] + '@' + msg[10:]
    else:
        msg = '@' + msg

    return msg


def FindRecord(id):
    uri = 'mongodb://' + DBHost
    Conn = MongoClient(uri)
    Conn.api.authenticate(DBUser, DBPass, DBName)
    database = Conn[DBName]
    mycollection = database.entries
    res = mycollection.find({"id": id})
    if res.count() == 0:
        return False
    else:
        return True


def insertDB(time, id, msg):
    uri = 'mongodb://' + DBHost
    Conn = MongoClient(uri)
    Conn.api.authenticate(DBUser, DBPass, DBName)
    database = Conn[DBName]
    mycollection = database.entries
    post = {"id": id, "time": time, "msg": msg}
    mycollection.insert(post)
    Conn.close()


def main():
    logger = logging.getLogger('main')

    field = {
        'minLngE6': 119618783,
        'minLatE6': 29912919,
        'maxLngE6': 121018722,
        'maxLatE6': 30573739,
    }

    mints = -1
    maxts=-1
    reverse=False
    tab='all'

    while True:
        try:
            if fetchCookie():
                break
        except CookieException:
            time.sleep(3)

    count = 0
    while True:
        count += 1

        with open('cookie') as cookies:
            cookies = cookies.read().strip()

        logger.info(getTime() + ": {} Fetching from Intel...".format(str(count)))

        while True:
            try:

                intel = ingrex.Intel(cookies, field)
                result = intel.fetch_msg(mints, maxts, reverse, tab)

                if result:
                    mints = result[0][1] + 1
                    break

            except CookieException:
                while True:
                    try:
                        if fetchCookie():
                            break
                    except CookieException:
                        time.sleep(3)
            except Exception:
                pass

        for item in result[::-1]:
            message = ingrex.Message(item)

            if message.ptype == 'PLAYER_GENERATED':
                # logger.info(getTime() + str(item))

                msg = formatMessage(item)
                if msg == 'Blocked':
                    logger.info(getTime() + " " + message.text)
                else:
                    msg = message.time + " " + msg
                    # logger.info(getTime() + " " + msg)
                    if FindRecord(message.guid) is False:
                        insertDB(message.time, message.guid, msg)
                        # sendMonitor(bot, msg)
                        sendMessge(bot, msg)

        time.sleep(10)

if __name__ == '__main__':
    readConfig()
    bot = telegram.Bot(BOT_TOKEN)

    while True:
        try:
            main()
        except Exception:
            sendMonitor(bot, 'Main Error')
