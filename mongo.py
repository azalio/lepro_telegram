from pymongo import MongoClient
import logging
import datetime


def mongo_connect(host, port, db):
    # client = MongoClient('localhost', 27017)
    client = MongoClient(host, port)
    db = client[db]
    # collection = db[collection]
    # return client, db, collection
    return db


def check_id(m_id, collection):
    if collection.find({"_id": m_id}).count() == 1:
        return False
    else:
        return True


def check_user_id(user_id, collection):
    cursor = collection.find_one({"user_id": user_id, "status": "complete"}, {"_id": 0, "user_id": 0})
    if cursor is not None:
        return cursor['lepra_oauth']
    else:
        cursor = collection.find_one({"user_id": user_id, "status": "prepare"})
        if cursor is None:
            cursor = collection.insert_one({'user_id': user_id, 'status': 'prepare'})
            return False
        if cursor is not None:
            return False


def get_users(collection):
    users = []
    cursor = collection.find({"status": "complete"}, {"_id": 0, "status": 0})

    for user in cursor:
        users.append(user)
    return users


def add_to_lepra_posts(post_id, user_id, collection):
    cursor = collection.update_one({"post_id": post_id},
                                   {"$addToSet": {"users": user_id}},
                                   upsert=True)


def check_lepra_post(post_id, user_id, collection):
    cursor = collection.find_one({"post_id": post_id}, {"_id": 0, "post_id": 0})
    if cursor:
        if user_id in cursor['users']:
            return True
        else:
            return False


def user_to_prepare(user_id, collection):
    result = collection.update_one({"user_id": user_id}, {"$set": {"status": "prepare"}})


def update_user_settings(user_id, command, collection):
    command_list = command.split('_')
    json_data = {command_list[0] + '_' + command_list[1]: command_list[2]}
    result = collection.update_one({"user_id": user_id},
                                   {"$set": json_data}, upsert=True)
    if result:
        return True


def delete_user(user_id, collection):
    cursor = collection.delete_one({"user_id": user_id})
    if cursor.deleted_count == 1:
        return True
    else:
        return False


def update_user_oauth(user_id, text, collection):
    result = collection.update_one({"user_id": user_id}, {"$set": {"status": "complete", "lepra_oauth": text}})
    if result.matched_count == 1:
        return True
    else:
        return False


def update_user_info(user_id, collection, **kwargs):
    kwargs['lastdate'] = datetime.datetime.utcnow()
    result = collection.update_one({"user_id": user_id}, {
        "$set": kwargs,
        "$inc": {"count": 1}})
    logging.debug(result.raw_result)
    if result.matched_count == 1:
        return True
    else:
        return False
