#!/usr/bin/env python3
from agent_pi.grpc_callbacks import unlock_callback
from agent_pi.database import UserCredentials
import argparse
import datetime


def run_process(user_id, username, authtoken, user_face):
    print("retreiving face encoding for user_id " + str(user_id))
    from facial_recognition import FaceEncoding, FacialRecognition

    encodings = FaceEncoding.from_json_str(user_face)
    user_credentials_request = {
        'id': str(user_id),
        'username': username,
        'authtoken': authtoken
    }

    def facerecog_unlock_callback():
        unlock_callback(user_credentials_request)

    def heartbeat_callback():
        user = UserCredentials.query.get(user_id)
        if user:
            print("{} user: {} pid: {} faceunlock waiting".format(
                datetime.datetime.now(), user.id, user.faceunlock_pid))
            if user.faceunlock_pid:
                return True
            else:
                print('heartbeat: user {} faceunlock_pid is None'.format(
                    user_id))
        else:
            print('heartbeat: user {} not found'.format(user_id))
        return False

    def killed_callback():
        print("faceunlock for user {} killed".format(user_id))
        user = UserCredentials.query.get(user_id)
        if user:
            user.stop_facial_recog()

    print("...")
    FacialRecognition(encodings, unlock_callback, heartbeat_callback,
                      killed_callback).run()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--user_id", help="user ID (in GCP db)")
    user_id = vars(ap.parse_args())["user_id"]
    user_creds = UserCredentials.query.get(user_id)
    if not user_creds:
        raise Exception("user_id {} not found".format(user_id))
    user_face = user_creds.user_face_model
    username = user_creds.username
    authtoken = user_creds.authtoken
    run_process(user_id, username, authtoken, user_face)
