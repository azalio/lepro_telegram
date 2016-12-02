#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json
from logging.handlers import SysLogHandler
import logging
import socket
import os
import sys

import config
import mongo
import telegram_bot
import util


def get_feed(oauth, feed_type, threshold_rating):
    url = 'https://leprosorium.ru/api/feeds/{feed_type}/?per_page=42&' \
          'threshold_rating={threshold_rating}'.format(feed_type=feed_type,
                                                       threshold_rating=threshold_rating)
    oauth = 'Bearer ' + oauth
    headers = {"Authorization": oauth, "Content-Type": "application/json"}
    try:
        result = requests.get(url, headers=headers)
    except Exception as exp:
        logger.exception("Can't get url")
        return False
    if result.status_code == 200:
        return result.json()
    elif result.status_code == 403 or result.status_code == 400:
        result = 'deny'
        return result
    else:
        logger.debug("Error: in status_code: {}".format(result.status_code))
        return False


def main():
    # print(collection)
    users = mongo.get_users(collection)
    # print(type(bot))
    for user in users:
        # print(user)
        chat_id = user['user_id']
        oauth = user['lepra_oauth']
        feed_type = user.get('feed_type', 'main')
        threshold_rating = user.get('threshold_rating', 'easy')
        feed = get_feed(oauth, feed_type, threshold_rating)
        # print(feed)
        if feed == 'deny':
            telegram_bot.get_user_oauth(chat_id, client_id, bot)
            continue
        for key in feed:
            # print key
            for post in feed[key]:
                send_to_user = ''
                post_id = post['id']
                read = mongo.check_lepra_post(post_id, chat_id, posts_collection)
                if read:
                    continue
                for key in post:
                    if key == 'body':
                        data = post[key]
                        data = util.strip_tags(data)
                        send_to_user = send_to_user + data + '\n'
                    elif key == '_links':
                        data = post[key][0]['href']
                        send_to_user = send_to_user + data
                if send_to_user:
                    result = telegram_bot.send_message(send_to_user, 'text', bot, chat_id)
                    if result:
                        mongo.add_to_lepra_posts(post['id'], chat_id, posts_collection)


if __name__ == '__main__':
    sys.path.append(os.path.dirname(__file__))
    # mongo
    host = config.conf['mongo']['host']
    port = int(config.conf['mongo']['port'])
    db = config.conf['mongo']['db']
    collection = config.conf['mongo']['collection']
    posts_collection = config.conf['mongo']['posts_collection']
    db = mongo.mongo_connect(host, port, db)
    collection = db[collection]
    posts_collection = db[posts_collection]

    KEY = config.conf['telegram']['token']
    bot = telegram_bot.create_bot(KEY)
    max_message_size = config.conf['telegram']['max_message_size']

    client_id = config.conf['lepra']['client_id']

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    try:
        syslog = SysLogHandler('/dev/log')
    except socket.error:
        syslog = SysLogHandler('/var/run/syslog')
    formatter = logging.Formatter(u'%(filename)s[LINE:%(lineno)d] %(message)s')
    syslog.setFormatter(formatter)
    logger.addHandler(syslog)

    main()
