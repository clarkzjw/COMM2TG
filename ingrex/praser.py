"Ingrex praser deal with message"
from datetime import datetime, timedelta
import platform
import os
import time

osname = platform.system()
if osname == "Linux":
    os.environ['TZ'] = 'Asia/Shanghai'
    time.tzset()

class Message(object):
    "Message object"
    def __init__(self, raw_msg):
        self.raw = raw_msg
        self.guid = raw_msg[0]
        self.timestamp = raw_msg[1]
        seconds, millis = divmod(raw_msg[1], 1000)
        time = datetime.fromtimestamp(seconds) + timedelta(milliseconds=millis)
        self.time = time.strftime('%Y/%m/%d %H:%M:%S:%f')[:-3]
        self.text = raw_msg[2]['plext']['text']
        self.ptype = raw_msg[2]['plext']['plextType']
        self.team = raw_msg[2]['plext']['team']
        self.type = raw_msg[2]['plext']['markup'][1][1]['plain']

