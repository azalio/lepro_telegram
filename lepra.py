#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import os
import sys
import time

import config
import mongo
import telegram_bot
import util


def markpost_as_read(post_id, oauth):
    url = 'https://leprosorium.ru/api/posts/{post_id}/view/'.format(post_id)
    oauth = 'Bearer ' + oauth
    headers = {"Authorization": oauth, "Content-Type": "application/json"}
    try:
        result = requests.post(url, headers=headers)
        if result.status_code == 200:
            config.logger.error("Mark post {post_id} as read".format(post_id))
            return True
        else:
            config.logger.error("Can't mark post {post_id} as read".format(post_id))
            return False
    except Exception as exp:
        config.logger.exception("Can't get url {}".format(exp))
        return False


def get_feed(oauth, feed_type, threshold_rating):
    url = 'https://leprosorium.ru/api/feeds/{feed_type}/?per_page=32&' \
          'threshold_rating={threshold_rating}'.format(feed_type=feed_type,
                                                       threshold_rating=threshold_rating)
    oauth = 'Bearer ' + oauth
    headers = {"Authorization": oauth, "Content-Type": "application/json"}
    try:
        result = requests.get(url, headers=headers)
    except Exception as exp:
        config.logger.exception("Can't get url {}".format(exp))
        return False
    if result.status_code == 200:
        return result.json()
    elif result.status_code == 403 or result.status_code == 400:
        config.logger.exception("Getting deny status code: oauth = {}, status_code = {}".format(oauth, result.status_code))
        result = 'deny'
        return result
    else:
        config.logger.exception("Error: in status_code: {}".format(result.status_code))
        return False


def main():
    users = mongo.get_users(collection)
    for user in users:
        chat_id = user['user_id']
        oauth = user['lepra_oauth']
        feed_type = user.get('feed_type', 'main')
        threshold_rating = user.get('threshold_rating', 'easy')
        markpost_read = user.get('markpost_read', 'false')
        feed = get_feed(oauth, feed_type, threshold_rating)
        if not feed:
            continue
        if feed == 'deny':
            telegram_bot.get_user_oauth(chat_id, client_id, bot)
            config.logger.error("Some auth error. User {}, move to prepare".format(chat_id))
            mongo.user_to_prepare(chat_id, collection)
            continue
        for key in feed:
            for post in feed[key]:
                send_to_user = ''
                post_id = post['id']
                config.logger.error("User id: {}".format(chat_id))
                config.logger.error("Post id: {}".format(post_id))
                read = mongo.check_lepra_post(post_id, chat_id, posts_collection)
                if read:
                    config.logger.error("User {} already read post: {}".format(chat_id, post_id))
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
                    config.logger.error("Send post {} to user {}".format(post_id, chat_id))
                    time.sleep(1)
                    result = telegram_bot.send_message(send_to_user, 'text', bot, chat_id)
                    if result:
                        config.logger.error("result is: {}".format(result))
                        if result == 'ban':
                            config.logger.error("User {} blocked bot, move to prepare".format(chat_id))
                            mongo.user_to_prepare(chat_id, collection)
                            continue
                        else:
                            mongo.add_to_lepra_posts(post['id'], chat_id, posts_collection)
                            if markpost_read == 'true':
                                markpost_as_read(post_id, oauth)


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

    main()
