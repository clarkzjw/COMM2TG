# -*- coding: utf-8 -*-

import os
import re
import time
import json
import logging
import inspect
import sys
from selenium import webdriver

import telegram
from pymongo import MongoClient

import ingrex

import aiohttp
import asyncio
import async_timeout

bot = None
BOT_TOKEN = ''
CHANNEL_NAME = ''
Email = ''
Passwd = ''
PhantomJSPath = ''
DBName = ''
DBUser = ''
DBPass = ''
DBHost = ''
BlockList = ''
LOG_FILENAME = 'voh.log'
TIME_ZONE='Asia/Shanghai'
minLngE6 = 0
minLatE6 = 0
maxLngE6 = 0
maxLatE6 = 0

class CookieException(Exception):
    pass


def get_time():
    return time.strftime('%x %X %Z')


def read_config():
    global Email
    global Passwd
    global BOT_TOKEN
    global CHANNEL_NAME
    global PhantomJSPath
    global DBName
    global DBUser
    global DBPass
    global DBHost
    global BlockList
    global LOG_FILENAME
    global minLngE6
    global minLatE6
    global maxLngE6
    global maxLatE6

    configfile = open("./config.json")
    config = json.load(configfile)
    Email = config["Email"]
    Passwd = config["Passwd"]
    BOT_TOKEN = config["BOT_TOKEN"]
    CHANNEL_NAME = config["CHANNEL_NAME"]
    PhantomJSPath = config["PhantomJSPath"]
    DBName = config["DBName"]
    DBUser = config["DBUser"]
    DBPass = config["DBPass"]
    DBHost = config["DBHost"]
    BlockList = config["BlockList"]
    minLngE6 = config["minLngE6"]
    minLatE6 = config["minLatE6"]
    maxLngE6 = config["maxLngE6"]
    maxLatE6 = config["maxLatE6"]

    os.environ['TZ'] = TIME_ZONE
    time.tzset()

    logging.basicConfig(level=logging.DEBUG,
                        filename=LOG_FILENAME,
                        encoding='utf8',
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-8s: %(levelname)-4s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def fetch_cookie():
    logger = logging.getLogger('fetch_cookie')
    logger.info(get_time() + ': Fetching Cookie...')

    driver = webdriver.PhantomJS(PhantomJSPath)
    driver.get('https://www.ingress.com/intel')

    # get login page
    link = driver.find_elements_by_tag_name('a')[0].get_attribute('href')
    driver.get(link)
    driver.get_screenshot_as_file('1.png')

    # simulate manual login
    driver.set_page_load_timeout(10)
    driver.set_script_timeout(20)
    driver.find_element_by_id('Email').send_keys(Email)
    driver.get_screenshot_as_file('2.png')
    driver.find_element_by_css_selector('#next').click()
    time.sleep(3)
    driver.find_element_by_id('Passwd').send_keys(Passwd)
    driver.get_screenshot_as_file('3.png')
    driver.find_element_by_css_selector('#signIn').click()
    time.sleep(3)
    driver.get_screenshot_as_file('4.png')

    # get cookies
    cookies = driver.get_cookies()

    csrftoken = ''
    SACSID = ''
    for key in cookies:
        if key['name'] == 'csrftoken':
            csrftoken = key['value']
        if key['name'] == 'SACSID':
            SACSID = key['value']

    if csrftoken == '' or SACSID == '':
        raise CookieException

    with open('cookie', 'w') as file:
        cookie = 'SACSID='+SACSID+'; csrftoken='+csrftoken+'; ingress.intelmap.shflt=viz; ingress.intelmap.lat=29.098418372855484; ingress.intelmap.lng=119.81689453125; ingress.intelmap.zoom=17'
        file.write(cookie)

    logger.info(get_time() + ': Fetching Cookie Succeed')
    driver.quit()
    return True


def send_message(bot, message, monitor=False):
    logger = logging.getLogger('send_message')
    while True:
        try:
            if monitor is True:
                bot.sendMessage(chat_id="@voamonitor", text=message)
            else:
                bot.sendMessage(chat_id=CHANNEL_NAME, text=message)
            logger.info(get_time() + ": sendMsg " + message)
            break
        except telegram.TelegramError:
            logger.error(get_time() + ": Send Message to Channel Failed")
            time.sleep(1)
        except Exception:
            logger.error(get_time() + ": Unexpected error: " + str(sys.exc_info()[0]) + " " + str(inspect.currentframe().f_lineno))
            time.sleep(1)


def find_message_record(id):
    uri = 'mongodb://' + DBHost
    conn = MongoClient(uri)
    conn.api.authenticate(DBUser, DBPass, DBName)
    database = conn[DBName]
    collection = database.entries
    count = collection.find({"id": id}).count()
    conn.close()
    if count == 0:
        return False
    else:
        return True


def insert_message_to_database(time, id, msg):
    uri = 'mongodb://' + DBHost
    conn = MongoClient(uri)
    conn.api.authenticate(DBUser, DBPass, DBName)
    database = conn[DBName]
    collection = database.entries
    post = {"id": id, "time": time, "msg": msg}
    collection.insert(post)
    conn.close()


def main():
    logger = logging.getLogger('main')

    # Lat & Lng of fetch region
    field = {
        'minLngE6': minLngE6,
        'minLatE6': minLatE6,
        'maxLngE6': maxLngE6,
        'maxLatE6': maxLatE6,
    }

    mints = -1
    maxts = -1
    reverse = False
    tab = 'all'

    # fetch cookie
    while True:
        try:
            if fetch_cookie():
                break
        except CookieException:
            logger.error(get_time() + ': Fetch Cookie Failed')
            time.sleep(3)
        except Exception:
            logger.error(get_time() + ": Unexpected error: " + str(sys.exc_info()[0]) + " " + str(inspect.currentframe().f_lineno))
            time.sleep(3)

    # fetch message
    count = 0
    while True:
        count += 1

        with open('cookie') as cookies:
            cookies = cookies.read().strip()
        logger.info(get_time() + ": {} Fetching from Intel...".format(str(count)))

        # fetch message per time
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
                        if fetch_cookie():
                            break
                    except CookieException:
                        time.sleep(3)
            except Exception:
                logger.error(get_time() + ": Unexpected error: " + str(sys.exc_info()[0]) + " " + str(inspect.currentframe().f_lineno))
                time.sleep(3)

        for item in result[::-1]:
            # Check spam message
            pattern = re.compile(BlockList)
            match = pattern.search(str(item))
            if match:
                continue

            message = ingrex.Message(item)
            if message.ptype == 'PLAYER_GENERATED':
                logger.info(get_time() + " " + message.msg)
                if find_message_record(message.guid) is False:
                    insert_message_to_database(message.time, message.guid, message.msg)
                    send_message(bot, message.msg, False)

        time.sleep(10)

if __name__ == '__main__':
    read_config()
    bot = telegram.Bot(BOT_TOKEN)

    while True:
        try:
            main()
        except Exception:
            send_message(bot, 'Main Unexpected error' + str(sys.exc_info()[0]) + " " + str(inspect.currentframe().f_lineno), True)
            time.sleep(3)