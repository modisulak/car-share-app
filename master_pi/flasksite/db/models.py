# credit to https://flask-marshmallow.readthedocs.io/en/latest/
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from wtforms.validators import StopValidation
from marshmallow.exceptions import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from marshmallow import fields as ma_fields
from master_pi.flasksite.forms import MaValidators
from master_pi.grpc.masterclient import MasterClient
import datetime
from werkzeug.utils import secure_filename
from master_pi import pushbullet

import uuid

mavalidator = MaValidators()

db = SQLAlchemy()
ma = Marshmallow()


def schema_validator(schema_load, json_data, kwargs):
    error = None
    try:
        schema_load(json_data, **kwargs)
    except StopValidation as e:
        error = str(e)
    except ValidationError as e:
        error = str(e)
    return error


class User(db.Model):
    """Data model for user accounts."""
    __tablename__ = "user_account"

    # validation
    username_max = 20
    password_max = 128
    name_max = 50
    email_max = 254

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(username_max), unique=True, nullable=False)
    pw_hash = db.Column(db.String(password_max), nullable=False)
    firstname = db.Column(db.String(name_max), nullable=False)
    lastname = db.Column(db.String(name_max), nullable=False)
    userType = db.Column(db.String(1), nullable=False)
    email = db.Column(db.String(email_max), nullable=False)
    userFace = db.relationship('UserFaceEncoding',
                               backref=db.backref('user_account', lazy=True))
    bd_addr = db.Column(db.String(64), nullable=True)
    pushbullet = db.Column(db.String(password_max), nullable=True)

    def __repr__(self):
        return "User({}, {})".format(self.username, self.pw_hash)

    @staticmethod
    def create_user(user_dict, commit=True):
        '''
        Creates a new user and commits to the database.

        :param user_dict : Dictionary containing user field that is being
                           created.
        :param commit : Specifies if needed to commit to the db.

        :return: Returns the new user.
        '''
        password_hashing_method = current_app.config['PASSWORD_HASHING_METHOD']
        user_dict['pw_hash'] = generate_password_hash(
            user_dict['password'], method=password_hashing_method)
        del user_dict['password']
        if not user_dict.get('userType', None):
            user_dict['userType'] = 'U'
        new_user = User(**user_dict)
        db.session.add(new_user)
        if commit:
            db.session.commit()
        return new_user

    @staticmethod
    def validate_input(json_data, **kwargs):
        error = schema_validator(user_schema.load, json_data, kwargs)
        if (error is None and secure_filename(json_data['username']) !=
                json_data['username']):
            error = "invalid username"
        return error

    def check_password(self, password):
        '''
        Checks if the password is correct
        :param password : Password entered by the user
        :return: Returns a boolean true if the password is correct else false.
        '''
        return check_password_hash(self.pw_hash, password)

    # def is_customer(self):
    #     '''
    #     Checks if a user is a customer
    #     :return: Returns a boolean true if the user is of type U.
    #     '''
    #     return self.userType == 'U'

    def update_userface(self, userface):
        """userface parameter is user face encoding serialised as json string\n
        updates User's UserFaceEncoding data"""
        user_face = UserFaceEncoding.query.filter_by(user_id=self.id).first()
        if user_face:
            db.session.delete(user_face)
            db.session.commit()
        user_face = UserFaceEncoding(encoding=userface, user_id=self.id)
        db.session.add(user_face)
        db.session.commit()

    @staticmethod
    def search(query):
        users = []
        qry_stmt = User.query
        if query:
            selects = [
                "id", "username", "firstname", "lastname", "userType", "email"
            ]
            filterable = [(k, v) for (k, v) in query.items()
                          if k in selects and len(v)]
            for (k, v) in filterable:
                qry_stmt = qry_stmt.filter(getattr(User, k).in_(v))

        users = qry_stmt.all()
        return users

    def set_field(self, key, value, commit=True):
        '''
        Update a specific field of a user
        '''
        if key == "locked":
            self.set_locked(bool(value))
        setattr(self, key, value)
        if commit:
            db.session.commit()

    def commit_changes(self):
        db.session.commit()


class UserFaceEncoding(db.Model):
    """Data model for user face encoding used with facial recognition."""
    __tablename__ = "userface_encoding"
    id = db.Column(db.Integer, primary_key=True)
    encoding = db.Column(db.Text(), nullable=False)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user_account.id'),
                        nullable=False,
                        unique=True)


class UserSchema(ma.Schema):
    id = ma_fields.Int()
    username = ma_fields.Str(validate=mavalidator.username)
    email = ma_fields.Email(validate=mavalidator.email)
    password = ma_fields.Str(validate=mavalidator.password)
    firstname = ma_fields.Str(validate=mavalidator.firstname)
    lastname = ma_fields.Str(validate=mavalidator.lastname)
    userType = ma_fields.Str()
    pushbullet = ma_fields.Str()

    class Meta:
        # fields to expose
        unknown = False
        fields = ("id", "username", "firstname", "lastname", "email",
                  "password", "userType", "pushbullet")
        exclude = ("password", )


user_schema = UserSchema()
users_schema = UserSchema(many=True)


class AuthToken(db.Model):
    """Data model for authentication tokens"""
    __tablename__ = "authentication_token"
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user_account.id'),
                        nullable=False)
    user_account = db.relationship('User',
                                   backref=db.backref('auth_tokens',
                                                      lazy=True))

    def __repr__(self):
        return "AuthToken({}, {})".format(self.token, self.user_id)

    @staticmethod
    def create_auth_token(user_id):
        '''
        Creates new AuthToken database entry
        :return: newly generated AuthToken database entry
        :rtype: AuthToken(db.Model){
            id<int>, token<str>, user_id<int>, user_account<User>
        }
        '''
        token = str(uuid.uuid4())
        new_token = AuthToken(user_id=user_id, token=token)
        db.session.add(new_token)
        db.session.commit()
        return new_token

    @staticmethod
    def from_token(auth_token):
        return AuthToken.query.filter_by(token=auth_token).first()


class AuthTokenSchema(ma.Schema):
    class Meta:
        # fields to expose
        fields = ("token", "user_id")


authTokenSchema = AuthTokenSchema()
authTokensSchema = AuthTokenSchema(many=True)


class Car(db.Model):
    """Data model for car accounts."""
    __tablename__ = "cars"

    # validation
    input_min = 3
    input_max = 255
    colour_max = 15

    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(input_max), nullable=False)
    body_type = db.Column(db.String(input_max), nullable=False)
    colour = db.Column(db.String(colour_max), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    locked = db.Column(db.Boolean(), nullable=False)
    lng = db.Column(db.Float(3, 6), nullable=False)
    lat = db.Column(db.Float(3, 6), nullable=False)
    costPerHour = db.Column(db.Float(5, 2), nullable=False)
    ipaddress = db.Column(db.String(input_max), nullable=True)

    field_permissions = {
        "A": [
            'make', 'body_type', 'colour', 'seats', 'locked', 'lat', 'lng',
            'costPerHour', 'ipaddress'
        ],
        "U": ['locked'],
        "E": ['locked']
    }

    @staticmethod
    def create_car(make, body_type, colour, seats, lng, lat, costPerHour,
                   locked):
        '''
        Creates a new car and adds to the database.

        :param make : Make of the car
        :param body_type : Body type of the car
        :param colour : Colour of the car
        :param seats : Number of seats in the car
        :param lng : Longitude of the car
        :param lat : Lattitude of the car
        :param costPerHour : Cost of the car per hour
        :param locked : Locked status of the car


        :return: Returns the new car.

        '''
        new_car = Car(make=make,
                      body_type=body_type,
                      colour=colour,
                      seats=seats,
                      lng=lng,
                      lat=lat,
                      costPerHour=costPerHour,
                      locked=locked)
        db.session.add(new_car)
        db.session.commit()
        return new_car

    # Added method to update the car status.
    def set_locked(self, locked):
        '''
        Set's the locked status of the car and commit to the database.
        '''
        self.locked = locked
        db.session.commit()
        # contact agent pi when car is locked and unlocked
        db.session.commit()
        mc = MasterClient(agent_ip=self.ipaddress)
        if self.locked:
            mc.LockCar()
        else:
            mc.UnlockCar()

    def set_location(self, lat, lng):
        '''
        Set's the location of the car in the database.
        '''
        self.lat = lat
        self.lng = lng
        db.session.commit()

    @staticmethod
    def search(query):
        cars = []
        qry_stmt = Car.query
        if query:
            selects = ["make", "body_type", "colour", "seats"]
            filterable = [(k, v) for (k, v) in query.items()
                          if k in selects and len(v)]
            for (k, v) in filterable:
                qry_stmt = qry_stmt.filter(getattr(Car, k).in_(v))

            cars = qry_stmt.all()

            if query.get('is_active') is not None:
                car_ids = {
                    booking.car_id
                    for booking in Booking.query.filter_by(active=True)
                }
                cars = [car for car in cars if car.id not in car_ids]
        else:
            cars = qry_stmt.all()

        if query and query.get('order_by') and 'price_asc' in query.get(
                'order_by'):
            cars.sort(key=lambda car: car.costPerHour)
        else:
            cars.sort(key=lambda car: car.costPerHour, reverse=True)

        return cars

    def set_field(self, key, value, commit=True, userType="U"):
        '''
        Update a specific field of a car
        '''
        if key in Car.field_permissions[userType]:
            # TODO, validate value
            if key == 'locked':
                self.set_locked(value)
            else:
                setattr(self, key, value)
            if commit:
                db.session.commit()
        else:
            raise Exception(
                "insufficient permissions for updating field {}".format(key))

    def commit_changes(self):
        db.session.commit()

    def bluetooth_proximity_unlock(self, bd_addr={}, user_id={}):
        user = User.query.get(user_id)
        user_cred_req = {
            'id': str(user_id),
            'username': user.username,
            'authtoken': AuthToken.create_auth_token(user_id).token
        }
        mc = MasterClient(agent_ip=self.ipaddress)
        return mc.BTProximityUnlock(bd_addr=bd_addr, user=user_cred_req)


class CarsSchema(ma.Schema):
    active = db.Column(db.Boolean(), nullable=True)


class Meta(ma.Schema):
    fields = ("id", "make", "body_type", "colour", "seats", "longitude",
              "latitude", "costperhour", "locked", "active")


car_schema = CarsSchema()
cars_schema = CarsSchema(many=True)


class Booking(db.Model):
    """Data model for booking accounts."""
    __tablename__ = "bookings"

    # validation
    input_min = 3
    input_max = 30
    colour_max = 15

    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=False, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    calendar_id = db.Column(db.String(256), nullable=True)
    userface_status = db.Column(db.Boolean, nullable=False)

    user_id = db.Column(db.Integer,
                        db.ForeignKey('user_account.id'),
                        nullable=False)
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    car = db.relationship('Car',
                          backref=db.backref('bookings', lazy='dynamic'))

    @staticmethod
    def create_booking(car_id,
                       user_id,
                       end_time,
                       active=True,
                       start_time=str(datetime.datetime.now()),
                       calendar_id=None,
                       userface_status=False):
        '''
        Creates a new booking and add's to the database.

        :param car_id : car_id of the car used to make the booking
        :param user_id : user_id of the user who created the booking
        :param active : Making the status of the booking to active
        :param start_time : Start time of the booking
        :param end_time : End time of the booking
        :param calendar_id : Google calendar_id for the booking

        :return: Returns the new booking.
        '''
        new_booking = Booking(active=active,
                              start_time=start_time,
                              end_time=end_time,
                              car_id=car_id,
                              user_id=user_id,
                              calendar_id=calendar_id,
                              userface_status=userface_status)
        db.session.add(new_booking)
        db.session.commit()
        # contact agent_pi, LoadUserCredentials
        user = new_booking.user
        token = AuthToken.create_auth_token(user.id).token
        mc = MasterClient(agent_ip=new_booking.car.ipaddress)
        mc.LoadUserCredentials(str(user.id), user.username, token,
                               user.userFace[0].encoding)
        return new_booking

    def delete_booking(self):
        # contact agent pi, delete user from agent pi
        # booking can only be deleted if user has not unlocked car
        MasterClient(agent_ip=self.car.ipaddress).UnloadUser()
        DeletedBooking.create_deleted_booking(self)
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def validate_input(json_data, **kwargs):
        return schema_validator(booking_schema.load, json_data, kwargs)

    def set_active(self, active):
        '''
        Set's the active status of the booking.
        '''
        self.active = active
        if not active:
            MasterClient(agent_ip=self.car.ipaddress).UnloadUser()
            # lock the car
            self.car.set_locked(True)
        db.session.commit()

    def set_endtime(self, end_time):
        '''
        Set's the end time of the booking.
        '''
        self.end_time = end_time
        db.session.commit()

    def set_calendarid(self, calendar_id):
        '''
        Set's google calander_id to the booking.
        '''
        self.calendar_id = calendar_id
        db.session.commit()

    def set_userface_status(self, userface_status):
        '''
        Added the userface status to the database.
        '''
        self.userface_status = userface_status
        db.session.commit()
        mc = MasterClient(agent_ip=self.car.ipaddress)
        mc.SetFaceUnlockStatus(userface_status)

    @staticmethod
    def parse_end_time(end_time_str):
        format = '%m/%d/%Y'  # The format
        end_time = datetime.datetime.strptime(end_time_str, format)
        return str(end_time)


class DeletedBooking(db.Model):
    """Data model for deleted bookings ("""
    __tablename__ = "deleted_bookings"
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=False, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    calendar_id = db.Column(db.String(256), nullable=True)
    userface_status = db.Column(db.Boolean, nullable=False)

    user_id = db.Column(db.Integer,
                        db.ForeignKey('user_account.id'),
                        nullable=False)
    user = db.relationship('User',
                           backref=db.backref('deleted_bookings', lazy=True))
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    car = db.relationship('Car',
                          backref=db.backref('deleted_bookings', lazy=True))
    orig_id = db.Column(db.Integer, nullable=False)
    deleted_time = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def create_deleted_booking(deleted_booking):
        bs = booking_schema.dump(deleted_booking)
        bs['orig_id'] = bs['id']
        bs['deleted_time'] = str(datetime.datetime.now())
        del bs['id']
        cb = DeletedBooking(**bs)
        db.session.add(cb)
        db.session.commit()


class BookingSchema(ma.Schema):
    id = ma_fields.Integer()
    active = ma_fields.Boolean()
    start_time = ma_fields.DateTime()
    end_time = ma_fields.DateTime()
    calendar_id = ma_fields.Str()
    userface_status = ma_fields.Boolean()
    car_id = ma_fields.Integer()
    user_id = ma_fields.Integer()

    class Meta:
        fields = ("id", "active", "start_time", "end_time", "calendar_id",
                  "userface_status", "car_id", "user_id")
        ordered = True


booking_schema = BookingSchema()
bookings_schema = BookingSchema(many=True)


class CarSchema(ma.Schema):
    id = ma_fields.Int()
    make = ma_fields.Str()
    body_type = ma_fields.Str()
    colour = ma_fields.Str()
    seats = ma_fields.Int()
    lng = ma_fields.Float()
    lat = ma_fields.Float()
    costPerHour = ma_fields.Float()
    locked = ma_fields.Boolean()
    ipaddress = ma_fields.Str()

    class Meta:
        fields = ("id", "make", "body_type", "colour", "seats", "lng", "lat",
                  "costPerHour", "locked")
        ordered = True


car_schema = CarSchema()
cars_schema = CarSchema(many=True)


class CarReport(db.Model):
    """Data for car reports given by the admins"""
    __tablename__ = "car_report"
    # validation
    input_min = 3
    input_max = 255
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(input_max), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    resolved = db.Column(db.Boolean, nullable=False)
    car = db.relationship('Car', backref=db.backref('reports', lazy=True))
    user_id = db.Column(db.Integer, nullable=True)

    @staticmethod
    def create_report(report_dict):
        '''
        :param report_dict: Report the admin has created
        { description, car_id, date_created, resolved }

        Creates a new report and add's to the database.

        :return: Returns the new report
        :rtype: CarReport
        '''
        new_report = CarReport(**report_dict)
        db.session.add(new_report)
        db.session.commit()
        engineers = User.query.filter(
            User.pushbullet.isnot(None)).filter_by(userType="E").all()
        tokens = [e.pushbullet.strip() for e in engineers]
        with current_app.app_context():
            message = "New car report: {description} - Car ID: {car_id}".format(
                description=new_report.description, car_id=new_report.car_id)
        pushbullet.batch_notify(tokens, "New Car Report", message)
        return new_report

    def update_report_status(self, resolve_status, userid):
        '''
        Set's the the resolve status of the report
        '''
        self.resolved = resolve_status
        self.user_id = userid
        db.session.commit()


class CarReportSchema(ma.Schema):
    class Meta:
        # fields to expose
        fields = ("id", "description", "car_id", "date_created", "resolved",
                  "user_id")


car_report_schema = CarReportSchema()
car_reports_schema = CarReportSchema(many=True)


class RequestLog(db.Model):
    """Data model that logs each request a user makes"""
    __tablename__ = "request_log"
    id = db.Column(db.Integer, primary_key=True)
    request_url = db.Column(db.String(2048), nullable=False)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user_account.id'),
                        nullable=True)
    date_created = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def create_request_log(request_log):
        '''
        :param request_log: dict containing all fields in new RequestLog row
        { request_url, user_id, date_created }

        Creates a new request log
        :return: new RequestLog entity
        :rtype: RequestLog instance
        '''
        new_request_log = RequestLog(**request_log)
        db.session.add(new_request_log)
        db.session.commit()
        return new_request_log
