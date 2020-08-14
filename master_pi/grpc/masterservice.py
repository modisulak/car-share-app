#!/usr/bin/env python3

# Reference: https://grpc.io/docs/quickstart/python.html#update-a-grpc-service
# Repository: https://github.com/grpc/grpc
from css_rpc import car_share_pb2, car_share_pb2_grpc
import grpc
import logging
import time
from agent_pi.utils import MASTERSERVICE_IP, AGENT_IP, ENABLE_BLUETOOTH
from flask import Flask
from concurrent import futures
from master_pi.flasksite.db.models import (User, Car, Booking, AuthToken, db,
                                           CarReport)
from voice_recognition import VoiceRecognition

# contacts the agent pi's grpc service from the master pi, requires agent pi's
# ip address on initialisation


class MasterService(car_share_pb2_grpc.MasterServiceServicer):
    def __init__(self, app):
        self.app = app

    def AgentCarInit(self, request, context):
        ap_address = AGENT_IP()
        ap_port = ap_address.split(":")[-1]
        agent_car_init_res = None
        user_credentials = None
        car = None
        with self.app.app_context():
            car_id = request.car_id
            # find user by finding car's active booking -> user_account
            bookings = Booking.query.filter_by(car_id=car_id,
                                               active=True).all()
            if (len(bookings) > 1):
                raise Exception("Multiple active bookings for the same car")
            elif len(bookings) == 1:
                booking = bookings.pop()
                user = booking.user
                if len(user.userFace) < 1:
                    raise Exception(
                        "user does not have facial recognition encodings")
                encoding = user.userFace[0].encoding
                user_credentials = {
                    "id": str(user.id),
                    "username": user.username,
                    "authtoken": AuthToken.create_auth_token(user.id).token,
                    "user_face_model": encoding,
                }
                car = booking.car
            else:
                # no active booking found for car, leave user_credentials empty
                car = Car.query.get(car_id)
            car.ipaddress = ap_address
            db.session.commit()
            agent_car_init_res = {
                "ip_address": ap_address,
                "port": ap_port,
                "locked": car.locked,
                "lng": float(car.lng),
                "lat": float(car.lat)
            }
            if user_credentials:
                agent_car_init_res["user_credentials"] = user_credentials
        print("Initialised Agent Car ID: {} - {} {}, IP: {}".format(
            car.id, car.make, car.body_type, car.ipaddress))
        return car_share_pb2.AgentCarInitResponse(**agent_car_init_res)

    def UnlockCarRequest(self, request, context):
        with self.app.app_context():
            username = request.username
            token = request.authtoken
            auth_token = AuthToken.from_token(token)
            car_id = getattr(request, 'car_id')
            if auth_token and auth_token.user_account.username == username:
                if not car_id:
                    booking = Booking.query.filter_by(
                        user_id=auth_token.user_account.id,
                        active=True).first()
                    if booking:
                        booking.car.set_locked(locked=False)
                        return car_share_pb2.GeneralResponse(status="200",
                                                             message="success")
                    else:
                        return car_share_pb2.GeneralResponse(
                            status="404",
                            message="Active booking with car not found")
                elif auth_token.user_account.userType == "E":
                    car = Car.query.get(car_id)
                    car.set_locked(locked=False)
                    return car_share_pb2.GeneralResponse(status="200",
                                                         message="success")
                else:
                    return car_share_pb2.GeneralResponse(
                        status="401", message="Unauthorized")
            else:
                return car_share_pb2.GeneralResponse(status="401",
                                                     message="Unauthorized")

    def ReportLocation(self, request, context):
        with self.app.app_context():
            car_id = request.car_id
            car = Car.query.get(car_id)
            lat = request.latitude
            lng = request.longitude
            car.set_location(lat, lng)
        return car_share_pb2.GeneralResponse(status="200", message="success")

    def VoiceRecognitionQuery(self, request, context):
        res = VoiceRecognition().start_voice_recog()
        return car_share_pb2.GeneralResponse(status="200", message=res)

    def SearchBluetooth(self, request, context):
        if ENABLE_BLUETOOTH():
            from bluetooth_services import BluetoothService
            print("{}: new bluetooth search".format(time.asctime()))
            res = BluetoothService.search()
            print(res)
            results = []
            for device in res:
                results.append(
                    car_share_pb2.BluetoothDevice(bd_addr=device[0],
                                                  device_name=device[1]))
            return car_share_pb2.BluetoothSearchResponse(results=results)

    def ResolveCarReport(self, request, context):
        with self.app.app_context():
            res = None
            user = request.user
            user_id = user.id
            token = user.authtoken
            auth_token = AuthToken.from_token(token)
            if auth_token and (str(auth_token.user_id) == user_id
                               and auth_token.user_account.userType == "E"):
                report = CarReport.query.get(request.report_id)
                if report:
                    if not report.resolved:
                        report.update_report_status(True, user_id)
                        res = car_share_pb2.GeneralResponse(status="200",
                                                            message="success")
                        db_data = User.query.get(user_id)
                        print("ENGINEER INFORMATION:")
                        print("Firstname: " + db_data.firstname)
                        print("Lastname: " + db_data.lastname)
                        print("Email: " + db_data.email)
                    else:
                        res = car_share_pb2.GeneralResponse(
                            status="400", messsage="Report already resolved")
            else:
                res = car_share_pb2.GeneralResponse(status="401",
                                                    message="Unauthorized")
            if not res:
                res = car_share_pb2.GeneralResponse(
                    status="400", message="Malformed Request")

            return res


_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def create_app(test_config):
    app = Flask('masterservice_flasksite')
    if test_config is None:
        from master_pi.instance.config import UseDevelopmentConfig
        app.config.from_object(UseDevelopmentConfig())
    else:
        app.config.from_object(test_config())
    db.init_app(app)
    return app


def serve(test_config=None):
    app = create_app(test_config)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    car_share_pb2_grpc.add_MasterServiceServicer_to_server(
        MasterService(app), server)
    ip = MASTERSERVICE_IP()
    server.add_insecure_port(ip)
    server.start()
    print("\nstarted! IP: {}".format(ip))
    if test_config is None:
        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop(0)
    return server


if __name__ == "__main__":
    print("loading...")
    logging.basicConfig()
    serve()
