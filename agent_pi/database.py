# credit to https://docs.python.org/3/library/subprocess.html#subprocess.Popen

from css_rpc import car_share_pb2_grpc, car_share_pb2
from agent_pi.utils import (FACE_RECOG_ENABLED, MASTERSERVICE_IP, IS_PI,
                            ENABLE_BLUETOOTH)
import grpc
# import subprocess
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import subprocess
from datetime import datetime, timedelta

app = Flask("agentservice_flasksite")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////{}/agent.db'.format(
    app.instance_path)
db = SQLAlchemy(app)

if IS_PI():
    from sense_hat import SenseHat
    import re
    sense = SenseHat()
    pixels = {"O": (0, 0, 0), "X": (0, 0, 255)}

    locked = """
    O O O O O O O O
    O X O O O O O O
    O X O O O O O O
    O X O O O O O O
    O X O O O O O O
    O X O O O O O O
    O X O O O O O O
    O X X X X X X O
    """

    unlocked = """
    O X O O O O X O
    O X O O O O X O
    O X O O O O X O
    O X O O O O X O
    O X O O O O X O
    O X O O O O X O
    O X O O O O X O
    O X X X X X X O
    """

    def str_matrix(string):
        string = re.sub("[\\s,]", "", string)
        return [pixels[pixel] for pixel in string]

    locked_matrix = str_matrix(locked)
    unlocked_matrix = str_matrix(unlocked)


class UserCredentials(db.Model):

    subprocesses = {}

    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    authtoken = db.Column(db.String(255), unique=True, nullable=False)
    user_face_model = db.Column(db.Text(), unique=True, nullable=True)
    car_id = db.Column(db.Integer(), db.ForeignKey('car.id'), nullable=True)
    faceunlock_pid = db.Column(db.String(4), nullable=True)
    user_type = db.Column(db.String(1), nullable=False)
    bd_addr = db.Column(db.String(64), nullable=True)

    @staticmethod
    def new_car_user(user_obj, user_type="U"):
        """
        :param kwargs: arguments to create a new UserCredentials db entry

        creates user from kwargs if user does not exist
        replaces user if user already exists
        if user_type is U and car is linked with another user, replaces with new

        :return: newly created UserCredentials db entry

        :rtype: UserCredentials instance"""
        # if user currently booked with car, delete current user
        if user_type == "U":
            current_user = (UserCredentials.query.filter_by(
                user_type="U", car_id=user_obj['car_id']).first())
            if current_user:
                db.session.delete(current_user)

        existing_user = UserCredentials.query.get(user_obj['id'])
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()
        user_obj['user_type'] = user_type
        user = UserCredentials(**user_obj)
        db.session.add(user)
        db.session.commit()
        return user

    def unload_user(self):
        # stop facial_recog process
        if self.faceunlock_pid:
            self.stop_facial_recog()
        db.session.delete(self)
        db.session.commit()

    def start_facial_recog(self):
        """
        If facial_recog_proccess is not None, throw error.
        else start a new facial recognition process, get it's process id (pid) -
        save pid to user
        """
        if not Car.query.get(self.car_id).locked:
            return
        self.stop_facial_recog()
        if FACE_RECOG_ENABLED():
            # "exec" causes script to inherit shell process
            proc = subprocess.Popen("exec agent_pi/face_recog.py -u {}".format(
                self.id),
                                    shell=True)
            print("new faceunlock process {}".format(proc))
            self.faceunlock_pid = proc.pid
            self.subprocesses[str(proc.pid)] = proc
            db.session.commit()
            print("faceunlock with PID: {} for user_id: {} started".format(
                proc.id, self.id))
        else:
            print("facial recognition not enabled")

    def stop_facial_recog(self):
        if FACE_RECOG_ENABLED():
            if self.faceunlock_pid:
                proc = self.subprocesses.get(str(self.faceunlock_pid))
                if proc:
                    proc.terminate()
                print("faceunlock pid: {} stopped for user: {}".format(
                    self.faceunlock_pid, self.id))
                self.faceunlock_pid = None
                db.session.commit()
            else:
                print("no faceunlock process for user {} running".format(
                    self.id))
            # sub = self.subprocesses[str(self.facial_recog_pid)]
            # sub.kill()
            # del self.subprocesses[str(self.facial_recog_pid)]
        else:
            print("facial recognition not enabled")
        db.session.commit()


class Car(db.Model):

    qr_code_subprocess = None

    __tablename__ = 'car'
    id = db.Column(db.Integer(), primary_key=True)
    locked = db.Column(db.Boolean(), nullable=False)
    ipaddress = db.Column(db.String(255), nullable=False)
    lng = db.Column(db.Float(10, 6), nullable=False)
    lat = db.Column(db.Float(10, 6), nullable=False)

    @staticmethod
    def create_car(id, locked, ipaddress, lng, lat):
        new_car = Car(id=id,
                      locked=locked,
                      ipaddress=ipaddress,
                      lng=lng,
                      lat=lat)
        db.session.add(new_car)
        db.session.commit()
        return new_car

    def update_car_statuslocked(self, new_status):
        if new_status:
            print("set pixels locked")
            if IS_PI():
                sense.set_pixels(locked_matrix)
        else:
            # stop facial recog process if car is unlocked
            print("set pixels unlocked")
            if IS_PI():
                sense.set_pixels(unlocked_matrix)
            user = UserCredentials.query.filter_by(car_id=self.id).first()
            if user:
                user.stop_facial_recog()
        self.locked = new_status
        db.session.commit()

    def report_location(self, lat, lng):
        """
        Check the master service's copy of the car's lat and lng against the
        the cars actual lat and lng. If the cars actual lat and lng is
        different, car call's master service's report location
        method and gives current lat lng.
        """
        if self.lng != lng or self.lat != lat:
            masterservice_ip = MASTERSERVICE_IP()
            with grpc.insecure_channel(masterservice_ip) as channel:
                stub = car_share_pb2_grpc.MasterServiceStub(channel)
                general_response = stub.ReportLocation(
                    car_share_pb2.Location(latitude=float(self.lat),
                                           longitude=float(self.lng),
                                           car_id=str(self.id)))
                print(general_response)

    def start_qr_code_resolve(self):
        if self.qr_code_subprocess:
            self.qr_code_subprocess.kill()
            self.qr_code_subprocess = None
        proc = subprocess.Popen("exec agent_pi/qr_code_subprocess.py",
                                shell=True)
        print("new qr code process {}".format(proc))
        Car.qr_code_subprocess = proc

    @staticmethod
    def stop_qr_subprocess():
        Car.qr_code_subprocess = None


class BluetoothSearch(db.Model):

    bluetooth_subprocess = None

    SEARCH_TIME = {"minutes": 5}

    __tablename__ = 'bt_search'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), primary_key=True)
    end_timestamp = db.Column(db.Integer, nullable=False)
    # POSIX timestamp
    user_credentials = db.relationship(
        'UserCredentials',
        backref=db.backref('bt_searches', cascade="all,delete"),
        lazy=True)
    car = db.relationship(
        'Car',
        backref=db.backref('bt_searches', cascade="all,delete"),
    )

    @staticmethod
    def delete_entry(user_id, car_id):
        result = BluetoothSearch.query.filter_by(user_id=user_id,
                                                 car_id=car_id).first()
        if result:
            result.delete_self()
        else:
            print("BluetoothSearch (car_id {}, user_id {}) not found".format(
                car_id, user_id))

    def delete_self(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def add_bluetooth_proximity_unlock(user_id, car_id):
        """
        :param user_id: id of UserCredentials to use for new bluetooth proximity
            unlock check

        adds user of `user_id` parameter to list of bluetooth devices to check
        for. Makes unlock request to masterservice with User's AuthToken when
        user's bd_addr discovered.
        Starts new bluetooth proximity unlock process if none running

        :return: expiration time in seconds
        """
        end_timestamp = 0
        if ENABLE_BLUETOOTH():
            # delete existing BluetoothSearch for user_id and car_id
            existing = BluetoothSearch.query.filter_by(user_id=user_id,
                                                       car_id=car_id).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()

            # time to stop check for user after duration of SEARCH_TIME
            end_timestamp = (
                datetime.now() +
                timedelta(**BluetoothSearch.SEARCH_TIME)).timestamp()
            new_check = BluetoothSearch(user_id=user_id,
                                        car_id=car_id,
                                        end_timestamp=end_timestamp)
            db.session.add(new_check)
            db.session.commit()

            if BluetoothSearch.bluetooth_subprocess:
                try:
                    BluetoothSearch.bluetooth_subprocess.kill()
                except Exception:
                    import traceback
                    traceback.print_exc()
                BluetoothSearch.bluetooth_subprocess = None

            proc = subprocess.Popen("exec agent_pi/bt_search_subprocess.py",
                                    shell=True)
            print("new bluetooth process {}".format(proc))
            BluetoothSearch.bluetooth_subprocess = proc
        else:
            print("BLUETOOTH NOT ENABLED")
        return end_timestamp

    @staticmethod
    def stop_subprocess():
        BluetoothSearch.bluetooth_subprocess = None
