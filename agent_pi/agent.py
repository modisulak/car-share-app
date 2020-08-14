#!/usr/bin/env python3

# Reference: https://grpc.io/docs/quickstart/python.html#update-a-grpc-service
# Repository: https://github.com/grpc/grpc

from css_rpc import car_share_pb2_grpc, car_share_pb2
import grpc
import logging
import time
import simplejson
from agent_pi.database import Car, UserCredentials, BluetoothSearch
from agent_pi.utils import MASTERSERVICE_IP, LAN_IP
from concurrent import futures
import argparse


def synchronise_agent(agent_init_response, car_id):
    print("synchronising agent:\n{}".format(agent_init_response))
    if Car.query.get(car_id) is None:
        Car.create_car(car_id, agent_init_response.locked,
                       agent_init_response.ip_address, agent_init_response.lng,
                       agent_init_response.lat)
    car = Car.query.get(car_id)
    car.update_car_statuslocked(agent_init_response.locked)
    car.report_location(agent_init_response.lat, agent_init_response.lng)

    user_creds = getattr(agent_init_response, "user_credentials")
    if user_creds.id and user_creds.authtoken:
        UserCredentials.new_car_user({
            'id': user_creds.id,
            'username': user_creds.username,
            'authtoken': user_creds.authtoken,
            'user_face_model': user_creds.user_face_model,
            'car_id': car_id
        })


class AgentService(car_share_pb2_grpc.AgentServiceServicer):
    def __init__(self, car_id):
        self.car_id = car_id
        print("Loaded car:\n{}".format(vars(self.car())))

    def car(self):
        return Car.query.get(self.car_id)

    def get_user(self):
        return UserCredentials.query.filter_by(car_id=self.car().id,
                                               user_type="U").first()

    def LoadUserCredentials(self, request, context):
        print("LOAD USER CREDS")
        try:
            user = UserCredentials.new_car_user({
                'car_id':
                self.car().id,
                'id':
                request.id,
                'username':
                request.username,
                'authtoken':
                request.authtoken,
                'user_face_model':
                request.user_face_model
            })
            print("Loaded user:\n{}".format(vars(user)))
            return car_share_pb2.GeneralResponse(status="200",
                                                 message="success")
        except BaseException as e:
            message = simplejson.dumps({"error": str(e)})
            return car_share_pb2.GeneralResponse(status="500", message=message)

    def SetFaceUnlockStatus(self, request, context):
        print("SET FACE UNLOCK STATE to " + str(request.running))
        try:
            if request.running:
                self.get_user().start_facial_recog()
            else:
                self.get_user().stop_facial_recog()

            return car_share_pb2.GeneralResponse(status="200",
                                                 message="success")
        except BaseException as e:
            message = simplejson.dumps({"error": str(e)})
            return car_share_pb2.GeneralResponse(status="500", message=message)

    def UnlockCar(self, request, context):
        print("UNLOCK CAR")
        self.car().update_car_statuslocked(False)
        # stop facial recognition process from master_pi
        return car_share_pb2.GeneralResponse(status="200", message="success")

    def LockCar(self, request, context):
        print("LOCK CAR")
        self.car().update_car_statuslocked(True)
        return car_share_pb2.GeneralResponse(status="200", message="success")

    def UnloadUser(self, request, context):
        print("UNLOAD USER")
        user = self.get_user()
        if user:
            user.unload_user()
        else:
            return car_share_pb2.GeneralResponse(status="404",
                                                 message="user not found")
        return car_share_pb2.GeneralResponse(status="200", message="success")

    def BTProximityUnlock(self, request, context):
        print("BT PROXIMITY UNLOCK")
        user = request.user
        if self.car().locked:
            engineer = UserCredentials.new_car_user(
                {
                    'id': user.id,
                    'username': user.username,
                    'authtoken': user.authtoken,
                    'bd_addr': request.bd_addr
                },
                user_type="E")
            end_time = BluetoothSearch.add_bluetooth_proximity_unlock(
                engineer.id,
                self.car().id)
            return car_share_pb2.GeneralResponse(message=str(end_time),
                                                 status='200')
        else:
            return car_share_pb2.GeneralResponse(
                message='car already unlocked', status='400')


def init_agent(car_id):
    masterservice_ip = MASTERSERVICE_IP()
    with grpc.insecure_channel(masterservice_ip) as channel:
        stub = car_share_pb2_grpc.MasterServiceStub(channel)
        response = stub.AgentCarInit(
            car_share_pb2.AgentCarInitRequest(car_id=car_id))
    return response


_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def run(car_id="1", testing=False):
    """ Contact MasterService  start AgentService with given address"""
    init_response = init_agent(car_id)
    synchronise_agent(init_response, car_id)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    car_share_pb2_grpc.add_AgentServiceServicer_to_server(
        AgentService(car_id), server)
    time.sleep(1)
    server.add_insecure_port("{}:{}".format(LAN_IP(), init_response.port))
    server.start()
    if not testing:
        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop(0)
    return server


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--car_id", default="1", help="car ID (in GCP db)")
    args = vars(ap.parse_args())
    logging.basicConfig()
    run(args["car_id"])
