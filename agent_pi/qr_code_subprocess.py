#!/usr/bin/env python3
from qr_code import QRCodeRecognition
from agent_pi.database import UserCredentials, Car
from agent_pi.grpc_callbacks import resolve_report_callback
import json


def matchfound_callback(barcode):
    data = json.loads(barcode)
    user_id = data['user_id']
    report_id = data['report_id']
    user = UserCredentials.query.get(user_id)
    if user:
        user_credentials_request = {
            'id': str(user_id),
            'authtoken': user.authtoken
        }
        response = resolve_report_callback(user_credentials_request, report_id)
        print("resolve_report response: {} - {}".format(
            response.status, response.message))
        return response
    else:
        print("USER OF ID: {} NOT FOUND ON AGENT PI".format(user_id))


def run_process():
    print("STARTING QRCodeRecognition")
    qr = QRCodeRecognition(matchfound_callback)
    qr.run()
    print("STOPPING QRCodeRecognition")
    Car.stop_qr_subprocess()


if __name__ == "__main__":
    run_process()
