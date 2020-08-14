#!/usr/bin/env python3

from agent_pi.grpc_callbacks import unlock_callback
from bluetooth_services import BluetoothSearch as BTSearchService
from agent_pi.database import BluetoothSearch, UserCredentials
from datetime import datetime
import time


def searchlist_callback():
    time.sleep(2)
    activelist = BluetoothSearch.query.all()
    searchlist = []
    print("BT ACTIVELIST {}".format(activelist))
    for e in activelist:
        if e.end_timestamp < datetime.now().timestamp():
            BluetoothSearch.delete_entry(e.user_id, e.car_id)
        else:
            searchlist.append(e.user_credentials.bd_addr)
    print("BT SEARCHLIST {}".format(searchlist))
    return searchlist


def matchfound_callback(match):
    user = UserCredentials.query.filter_by(bd_addr=match).first()
    print("MATCH FOUND USER ID: {}, {}".format(user.id, user))
    bt_searches = user.bt_searches
    for search in bt_searches:
        user_cred_req = {
            'id': str(user.id),
            'username': user.username,
            'authtoken': user.authtoken,
            'car_id': str(search.car_id),
        }
        print("UNLOCK REQUEST {}".format(user_cred_req))
        unlock_callback(user_cred_req)
        search.car.start_qr_code_resolve()
        search.delete_self()


def run_process():
    print("STARTING BTSearchService")
    bts = BTSearchService(searchlist_callback, matchfound_callback)
    bts.run()
    print("STOPPING BTSearchService")
    BluetoothSearch.stop_subprocess()


if __name__ == "__main__":
    run_process()
