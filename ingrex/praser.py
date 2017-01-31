from datetime import datetime, timedelta
import re
import os
import time


class Message(object):
    def __init__(self, raw_msg):
        os.environ['TZ'] = 'Asia/Shanghai'
        time.tzset()

        seconds, millis = divmod(raw_msg[1], 1000)
        timestamp = datetime.fromtimestamp(seconds) + timedelta(milliseconds=millis)
        self.time = timestamp.strftime('%Y/%m/%d %H:%M:%S:%f')[:-3]

        self.raw = raw_msg
        self.guid = raw_msg[0]
        self.timestamp = raw_msg[1]
        self.text = raw_msg[2]['plext']['text']
        self.ptype = raw_msg[2]['plext']['plextType']
        self.team = raw_msg[2]['plext']['team']
        self.type = raw_msg[2]['plext']['markup'][1][1]['plain']

        self.msg = ''
        self.markup = raw_msg[2]['plext']['markup']

        for mark in self.markup:
            if mark[0] == 'SECURE':
                self.msg += mark[1]['plain']
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
                self.msg += player

            elif mark[0] == 'PLAYER' or mark[0] == 'AT_PLAYER':
                player = mark[1]['plain']
                team = mark[1]['team']

                self.msg += player
                if team == 'RESISTANCE':
                    self.msg += ' 🐳'
                elif team == 'ENLIGHTENED':
                    self.msg += ' 🐸'

            elif mark[0] == 'TEXT':
                self.msg += mark[1]['plain']

        pattern = re.compile('\[secure\]')
        match = pattern.search(self.msg)
        if match:
            if self.msg.find(':') != -1:
                self.msg = self.msg[:9] + '@' + self.msg[9:]
            else:
                self.msg = self.msg[:10] + '@' + self.msg[10:]
        else:
            self.msg = '@' + self.msg

        self.msg = self.time + self.msg
