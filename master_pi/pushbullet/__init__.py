import requests
import json
import threading
import logging


def send_notification(access_token, title, body):
    """
    :param access_token: string user's pushbullet api access token
    :param title: string of notification title
    :param body: string of body of notification
    Send a notification to a pushbullet user using their access token
    :return: response from http request
    :rtype: requests response entity
    """
    req_data = {"type": "note", "title": title, "body": body}
    return requests.post("https://api.pushbullet.com/v2/pushes",
                         data=json.dumps(req_data),
                         headers={
                             'Authorization': 'Bearer ' + access_token,
                             'Content-Type': 'application/json'
                         })


def batch_notify(users, title, body, is_thread=False):
    if is_thread:
        for token in users:
            send_notification(token, title, body)
            logging.info("pushbullet token {} notified of {}".format(
                token, title))
    else:
        t = threading.Thread(target=batch_notify,
                             args=(users, title, body, True))
        t.start()
        return t
