#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import time
import telepot
import requests

import config
import mongo
import util


def create_bot(bot_token):
    return telepot.Bot(bot_token)
    # return telepot.Bot(bot_token)


def get_user_oauth(chat_id, client_id, bot):
    url = 'https://leprosorium.ru/oauth/?response_type=token&client_id={}'.format(client_id)
    data = u"Пожалуйста, авторизуйте приложение для работы с leprosorium.ru \n" + url
    send_message(data, 'text', bot, chat_id)


def send_message(data, message_type, bot, chat_id=12452435):
    try:
        if message_type == 'text':
            chunks = util.split_text_to_chanks(data, 4095, [])
            for chunk in chunks:
                # print(len(chunk))
                bot.sendMessage(chat_id, chunk)
        if message_type == 'photo':
            with open(data, 'r') as f:
                bot.sendPhoto(chat_id, f)
    except telepot.exception.TooManyRequestsError as exp:
        config.logger.exception("Error: Too Many Requests")
        sleep = exp[-1]['parameters']['retry_after']
        config.logger.debug("Too fast, sleeping: {}".format(sleep))
        # print(data)
        time.sleep(sleep)
        return send_message(data, message_type, bot, chat_id)
    except requests.exceptions.ReadTimeout as exp:
        config.logger.exception("Error: Read Timeout")
        return False
    except telepot.exception.TelegramError as exp:
        config.logger.exception("Error: TelegramError")
    else:
        return True


def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    try:
        last_name = msg.get('chat', {}).get('last_name', '')
        first_name = msg.get('chat', {}).get('first_name', '')
        username = msg.get('chat', {}).get('username', '')
        mongo.update_user_info(chat_id, collection, last_name=last_name,
                                                  first_name=first_name,
                                                  username=username)
    except Exception as exp:
        config.logger.exception("Error: Can't update user info {}".format(exp))
    oauth = mongo.check_user_id(chat_id, collection)
    if oauth:
        # user_exist_and_ok = True
        try:
            entities = msg.get('entities', None)[0]
            # print(entities)
            if entities:
                command_type = entities.get('type', None)
                # print(command_type)
                if command_type == 'bot_command':
                    result = catch_bot_command(msg, chat_id)
                    # print(result)
        except TypeError as exp:
            config.logger.exception("Error: TypeError")
            text = u"К сожалению, я не настолько умный.\nЯ понимаю только "\
                   u"три команды, о которых вы можете узнать выполнив команду:\n"\
                   u"/help"
            send_message(text, 'text', bot, chat_id)
        except Exception as exp:
            config.logger.exception("Error: message analysis")
    else:
        # user_exist_and_ok = False
        try:
            entities = msg.get('entities', None)[0]
            # print(entities)
            if entities:
                command_type = entities.get('type', None)
                # print(command_type)
                if command_type == 'bot_command':
                    result = catch_bot_command(msg, chat_id)
                    if result:
                        if result['command'] == 'start':
                            oauth = result.get('oauth', None)
        except Exception as exp:
            config.logger.exception("Error: message analysis")
        if not oauth:
            get_user_oauth(chat_id, client_id, bot)
        else:
            text = u"Все готово для работы с ботом.\n" \
                   u"Дополнительные настройки можно увидеть, выполнив команду:\n"\
                   u"/settings"
            send_message(text, 'text', bot, chat_id)


def catch_bot_command(msg, chat_id):
    result = {}
    settings_command = ['feed_type_personal', 'feed_type_main', 'feed_type_mixed',
                        'threshold_rating_easy', 'threshold_rating_medium',
                        'threshold_rating_normal', 'threshold_rating_hard',
                        'threshold_rating_hardcore', 'threshold_rating_nightmare']
    try:
        command_list = msg['text'].split()
        command = command_list[0].lower().lstrip('/')
        # print(command)
        if command == 'start' and len(command_list) > 1:
            oauth_key = command_list[1]
            mongo.update_user_oauth(chat_id, oauth_key, collection)
            oauth = mongo.check_user_id(chat_id, collection)
            result['command'] = command
            result['oauth'] = oauth
        elif command == 'start' and len(command_list) < 2:
            text = u'Команда /start должна вызываться вместе с токеном от сайта.'
            send_message(text, 'text', bot, chat_id)
        elif command == 'stop':
            result = mongo.delete_user(chat_id, collection)
            if result:
                text = u'Рады были вас видеть!'
                send_message(text, 'text', bot, chat_id)
                data = "img/stop.jpg"
                send_message(data, 'photo', bot, chat_id)
        elif command == 'help':
            text = u"""Поддерживаются следующие команды:
/help - эта помощь
/settings - настройки ленты и её содержимого
/stop - прекращение работы с ботом
Пообщаться с создателем бота можно в телеграме @azalio
            """
            send_message(text, 'text', bot, chat_id)
        elif command == 'settings':
            data = u"""
Настройка канала:
            /feed_type_personal - только подлепры
            /feed_type_main - главная без подлепр
            /feed_type_mixed - главная с подлепрами

Настройка отображения:
            /threshold_rating_easy - 1000+
            /threshold_rating_medium - 500
            /threshold_rating_normal - 250
            /threshold_rating_hard - 50
            /threshold_rating_hardcore - 0
            /threshold_rating_nightmare - all
            """
            # print(text)
            send_message(data, 'text', bot, chat_id)
            result['command'] = command_list[0]
        elif command in settings_command:
            mongo.update_user_settings(chat_id, command, collection)
    except Exception as exp:
        config.logger.exception("Error: in catch_bot_command function")
        return False
    else:
        return result


if __name__ == '__main__':
    sys.path.append(os.path.dirname(__file__))

    KEY = config.conf['telegram']['token']
    MY_ID = config.conf['telegram']['my_id']
    max_message_size = config.conf['telegram']['max_message_size']
    # mongo
    host = config.conf['mongo']['host']
    port = int(config.conf['mongo']['port'])
    db = config.conf['mongo']['db']
    collection = config.conf['mongo']['collection']
    db = mongo.mongo_connect(host, port, db)
    collection = db[collection]
    # lepra
    client_id = config.conf['lepra']['client_id']

    text_documents = ['text', 'contact', 'location', 'venue']
    file_documents = ['photo', 'document', 'audio', 'video', 'voice']

    bot = create_bot(KEY)
    bot.message_loop(handle)
    # print 'Listening ...'

# Keep the program running.
    while 1:
        time.sleep(10)
