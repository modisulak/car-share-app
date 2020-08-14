# Credit to https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/;
from flask import Blueprint, request, make_response, g, jsonify
from master_pi.flasksite.db.models import (db, User, user_schema, users_schema,
                                           AuthToken, authTokenSchema, Car,
                                           cars_schema, car_schema, Booking,
                                           booking_schema, bookings_schema,
                                           CarReport, car_report_schema,
                                           car_reports_schema)
from datetime import datetime, timedelta
from master_pi.grpc.masterclient import MasterClient
from agent_pi.utils import MASTERSERVICE_IP
import functools
api_bp = Blueprint('api', __name__, url_prefix='/api')


def auth_token_required(user_type_required=["U", "A", "E",
                                            "M"]):  # taken the Auth Token.
    """
    Retreives Auth token from request, ``g.auth_token`` takes precedence,
    otherwise request.headers.get('Authorization') is checked
    :return: ``wrapped_view`` which will execute wrapped view if auth token
    exists and auth_token.user_account.userType is in ``user_type_required``
    argument, otherwise returns http errror 401 Unauthorized
    :rtype: function
    """
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):
            result = None
            token = None
            if hasattr(g, 'auth_token') and g.auth_token:
                token = g.auth_token
            else:
                token = request.headers.get('Authorization', None)
            if token:
                auth_token = AuthToken.from_token(token)
                if auth_token and (auth_token.user_account.userType in
                                   user_type_required):
                    result = view(*args, auth_token=auth_token, **kwargs)
            if not result:
                result = make_response(jsonify(error="Unauthorized"), 401)
            return result

        return wrapped_view

    return decorator


def load_json(*json_req_args):
    """
    :param *json_req_args: string, required fields in request json data
    Load json from localproxy g or request.get_json then check if required
    arguments are present in json, or else return http error 400 malformed
    request to the user. loaded json data can be accessed by wrapped function
    using kw argument `json_data`

    :return: ``wrapped_view``
    :rtype: Function
    """
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):
            json_data = []
            if kwargs.get('json_data'):
                json_data = kwargs['json_data']
                del kwargs['json_data']
            elif hasattr(g, 'api_request_json'):
                json_data = g.api_request_json.copy()
                delattr(g, 'api_request_json')
            elif request.is_json:
                json_data = request.get_json()
            result = None
            # if (json_data is not empty and json_data contains all of
            # json_req_args) is false then request is malformed, respond error
            if not (json_data and all(x in json_data for x in json_req_args)):
                result = make_response(
                    jsonify(error="malformed request, missing {}".format([
                        x.strip() for x in json_req_args if x not in json_data
                    ])), 400)
            else:
                result = view(*args, json_data=json_data, **kwargs)
            return result

        return wrapped_view

    return decorator


def load_query_params(view):
    '''
    Retrieve query parameters from request, kwargs['query_params'] takes
    precedence, otherwise request.args is used
    :return: wrapped view with query_params inserted into wrapped view's kwargs
    :rtype: function
    '''
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        query_params = kwargs.get('query_params')
        if query_params is None:
            kwargs['query_params'] = request.args
        return view(*args, **kwargs)

    return wrapped_view


def validate_patch(supported):
    '''
    :param supported: list of strings representing supported fields
    :param json_data: dict of json data from http request with json_data
    Ensures fields in json data of patch request are supported by patch method
    :return: if request contains only supported fields, wrapped view with
    supported list inserted into wrapped view's kwargs, otherwise http error 400
    Bad Request
    :rtype: wrapped_view decorator function
    '''
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):
            res = None
            json_data = kwargs['json_data']
            unsupported = [
                key for key in json_data.keys() if key not in supported
            ]
            if unsupported:
                res = make_response(
                    jsonify(
                        {"error": "keys {} unsupported".format(unsupported)}),
                    400)
            else:
                res = view(*args, **kwargs)
            return res

        return wrapped_view

    return decorator


class AuthApi:
    @staticmethod
    @api_bp.route('/auth/register', methods=['POST'])
    @load_json('username', 'password', 'firstname', 'lastname', 'email')
    def auth_register(json_data={}):
        username = json_data['username']
        res = None
        error = User.validate_input(json_data)
        if error:
            res = make_response(jsonify({"error": error}), 400)
        else:
            # check username is unique
            user = User.query.filter_by(username=username).first()
            if user:
                res = make_response(jsonify({"error": 'username taken'}), 400)
            else:
                # insert new user
                new_user = User.create_user(json_data)
                res = make_response(user_schema.jsonify(new_user), 201)

        return res

    @staticmethod
    @api_bp.route('/auth/login', methods=['POST'])
    @load_json('username', 'password')
    def auth_login(json_data={}):
        username = json_data['username']
        password = json_data['password']

        res = None

        error = User.validate_input(json_data, partial=True)
        if error:
            res = make_response(jsonify({"error": error}), 400)
        # get user
        else:
            user = User.query.filter_by(username=username).first()
            if not user:
                res = make_response(
                    jsonify({"error": "Incorrect login information."}), 404)
            elif not user.check_password(password):
                res = make_response(
                    jsonify({"error": "Incorrect login information."}), 400)
            else:
                new_token = AuthToken.create_auth_token(user.id)
                res_data = authTokenSchema.dump(new_token)
                res_data['userType'] = user.userType
                res = jsonify(res_data)

        # return api token
        return res

    @staticmethod
    @api_bp.route('/auth/user', methods=['PATCH'])
    @auth_token_required()
    @load_json()
    @validate_patch({'userFace', 'bd_addr'})
    def auth_update_user(auth_token=None, json_data={}):
        # fields supported:
        #   -   userFace field, stores the pickle containing
        #       their facial recognition encoding.
        #  -    bd_addr, stores bd address of user's registered bluetooth device
        user = auth_token.user_account
        for (key, value) in json_data.items():
            if key == 'userFace':
                user.update_userface(value)
            else:
                user.set_field(key, value)
            # TODO look up actively booked car and send to car
        return make_response(user_schema.jsonify(g.user), 200)


class CarsApi:
    @staticmethod
    @api_bp.route("/cars", methods=["GET"])
    @auth_token_required()
    @load_query_params
    def get_all_cars(auth_token=None, query_params={}):
        '''
        Gets all the cars that are currently locked from the database

        :param auth_token: The users authentication token to ensure only logged
                           users can access.
        :param query_params: Used to search the data

        :return Returns the list of cars in json format.
        '''
        res = None
        if query_params.get("search_data"):
            fields = {
                "id": db.session.query(Car.id).distinct().all(),
                "make": db.session.query(Car.make).distinct().all(),
                "body_type": db.session.query(Car.body_type).distinct().all(),
                "colour": db.session.query(Car.colour).distinct().all(),
                "seats": db.session.query(Car.seats).distinct().all(),
            }
            res = jsonify(fields)
        else:
            if query_params:
                filter = ["", "on", "submit"]
                query_params = {
                    k: [x for x in v if x not in filter]
                    for (k, v) in query_params.to_dict(flat=False).items()
                    if k not in filter
                }
            cars = Car.search(query_params)
            car_data = cars_schema.dump(cars)
            for (d_car, car) in zip(car_data, cars):
                d_car['active'] = len(
                    car.bookings.filter_by(active=True).all()) > 0
            res = jsonify(car_data)
        return res

    @staticmethod
    @api_bp.route("/cars/<id>", methods=["GET"])
    @auth_token_required()
    def get_car(id, auth_token=None):
        '''
        Gets one single car from the database

        :param auth_token: The users authentication token to ensure only
            authorised users can access sensitive car data.
        :param id: car_id used to get one single car

        :returns the one single car in json format.
        '''
        car = Car.query.get(id)
        # car_data = car_schema.dump(car)
        # booking = Booking.query.filter_by(active=True, car_id=id).first()
        # if booking and booking.user_id != auth_token.user_account.id:
        #     car_data['lat'] = 0
        #     car_data['lng'] = 0
        #     car_data['locked'] = True
        return car_schema.jsonify(car)

    @staticmethod
    @api_bp.route('/cars/<id>', methods=['PATCH'])
    @auth_token_required()
    @load_json()
    @validate_patch({
        'locked', 'make', 'body_type', 'colour', 'seats', 'costPerHour', 'lat',
        'lng'
    })
    def patch_car(id, auth_token={}, json_data={}):
        '''
        Updates the attributes locked in the car table of the database

        :param auth_token: The users authentication token to ensure only logged
                           users can access.
        :param id: car_id used to get one single car.
        :param json_data: Json data from the request.

        :return Returns a jsonified car schema with a success message of 200
        '''
        res = None
        car = Car.query.get(id)
        booking = Booking.query.filter_by(car_id=id, active=True).first()
        user_type = auth_token.user_account.userType
        if not car:
            res = make_response(jsonify(error="car not found"), 404)
        elif user_type == 'U' and (
                not booking or booking.user.id != auth_token.user_account.id):
            res = make_response(
                jsonify(error="Unauthorized, user cannot access car"), 401)
        else:
            # input validation rules
            # "U" user cannot lock car again while booking still active
            errors = []
            if user_type == 'U' and (json_data.get('locked', None) is True
                                     and car.locked is False):
                errors.append("User must return car before locking again")
            if errors:
                res = make_response(jsonify(error=errors), 400)
            else:
                for (key, value) in json_data.items():
                    # TODO look up actively booked car and send to car
                    try:
                        car.set_field(key,
                                      value,
                                      commit=False,
                                      userType=user_type)
                    except Exception as e:
                        errors.append(str(e))
                try:
                    car.commit_changes()
                    res = make_response(car_schema.jsonify(car), 200)
                except Exception as e:
                    res = make_response(jsonify(error=e), 400)
        return res

    @staticmethod
    @api_bp.route('/cars', methods=['POST'])
    @auth_token_required(["A"])
    @load_json('make', 'body_type', 'colour', 'seats', 'costPerHour', 'lat',
               'lng')
    @validate_patch(
        {'make', 'body_type', 'colour', 'seats', 'costPerHour', 'lat', 'lng'})
    def add_car(json_data={}):
        '''
         Adds a car to the database.

        :param auth_token: The users authentication token to ensure only logged
                           admins can access.
        :param json_data: Json data from the request.

        :return Returns a jsonified car schema with a success message of 200
        '''
        res = None

        try:
            car = Car.create_car(json_data['make'], json_data['body_type'],
                                 json_data['colour'], json_data['seats'],
                                 json_data['costPerHour'], json_data['lat'],
                                 json_data['lng'], True)
            if car is not None:
                res = make_response(car_schema.jsonify(car), 200)
        except Exception as e:
            res = make_response(
                jsonify(error="failed to add car: {}".format(e)), 500)
        return res

    class Bluetooth:
        @staticmethod
        @api_bp.route('/cars/<car_id>/bluetooth/unlock', methods=['POST'])
        @auth_token_required(["E"])
        @load_json('bd_addr')
        def proximity_unlock(car_id, auth_token={}, json_data={}):
            '''
            :auth_token_required: "E" userType
            :param car_id: - target car
            :param json_data: - dict obj of format {'bd_addr': <str>}
            Requests a car to unlock when specified `bd_addr` comes into
            proximity of car's bluetooth peripheral
            :return: obj containing expiration time of proximity unlock search
            :rtype: json_data = {'expiration_time': <time in seconds>}
            '''
            res = None
            car = Car.query.get(car_id)
            if not car:
                res = make_response(jsonify(error="car not found"), 404)
            else:
                try:
                    gen_res = car.bluetooth_proximity_unlock(
                        bd_addr=json_data['bd_addr'],
                        user_id=auth_token.user_account.id)
                    if gen_res.status == '200':
                        res = make_response(
                            jsonify(expiration_time=float(gen_res.message)),
                            200)
                    else:
                        res = make_response(jsonify(error=gen_res.message),
                                            int(gen_res.status))
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    res = make_response(
                        jsonify(error="request failed: {}".format(e)), 500)
            return res


class BookingApi:
    @staticmethod
    @api_bp.route('/bookings/', methods=['GET'])
    @auth_token_required()
    @load_query_params
    def get_bookings(auth_token=None, query_params={}):
        '''
        Gets all the bookings related to the user from the database.
        Set query parameter user_id to select only bookings of a specific user

        :param auth_token: The users authentication token to ensure only logged
                           users can access.

        :return Returns a json data of bookings.
        :rtype: http response with json string of list of serialised bookings
        '''
        res = None
        bookings = Booking.query.order_by(Booking.start_time.desc()).order_by(
            Booking.id.desc())
        qp_user_id = query_params.get('user_id')
        # input validation
        if auth_token.user_account.userType != "A":
            user_id = auth_token.user_account.id
            if qp_user_id is None or user_id != qp_user_id:
                res = make_response(jsonify(error="Unauthorized"), 401)
        # query formation
        if res is None:
            if qp_user_id:
                bookings = bookings.filter_by(user_id=qp_user_id)
            bookings = bookings.all()
            booking_data = bookings_schema.dump(bookings)
            for (booking, b_data) in zip(bookings, booking_data):
                b_data['car'] = car_schema.dump(booking.car)
            res = jsonify(booking_data)
        return res

    @staticmethod
    @api_bp.route("/bookings", methods=["POST"])
    @auth_token_required()
    @load_json("car_id", "end_time")
    def new_booking(json_data={}, auth_token=None):
        '''
        Creates a new booking and add's that to the booking table in the
        database

        :param auth_token: The users authentication token to ensure only logged
                           users can access.
        :param json_data: Json data from the request.

        :return Returns a jsonified car schema with a success message of 201
                named "CREATED".
        '''

        res = None
        error = Booking.validate_input(json_data, partial=True)
        end_time = datetime.strptime(json_data['end_time'],
                                     '%Y-%m-%d %H:%M:%S')
        if not error:
            if end_time < datetime.now() + timedelta(hours=1):
                error = "end date too soon"

            elif Booking.query.filter_by(car_id=json_data['car_id'],
                                         active=True).first():
                # only allow a user to book a car if it is not actively
                # booked
                error = "car is not available"
            elif Booking.query.filter_by(user_id=auth_token.user_account.id,
                                         active=True).first():
                # only allow a user to book a if they do not have any
                # active bookings
                error = "cannot make a booking while another booking is active"
            elif len(auth_token.user_account.userFace) < 1:
                # only allow a user to book a car if the have facial
                # recognition
                error = "facial recognition is required to make a booking"

        if error:
            res = make_response(jsonify({"error": error}), 400)
        else:
            user = auth_token.user_account
            car_id = json_data['car_id']
            end_time = json_data['end_time']
            new_booking = Booking.create_booking(
                car_id=car_id,
                user_id=user.id,
                end_time=end_time,
            )
            res = make_response(booking_schema.jsonify(new_booking), 201)
        # create new booking
        return res

    @staticmethod
    @api_bp.route("/bookings/<id>", methods=["GET"])
    @auth_token_required()
    def get_booking(id, auth_token={}):
        '''
        Get's one single booking from the database.

        :param auth_token: The users authentication token to ensure only logged
                           users can access.
        :param id: car_id used to get one single car.

        :return Returns a jsonified data of the booking.
        '''
        booking = Booking.query.get(id)
        if not booking or (auth_token.user_account.userType != "A"
                           and booking.user_id != auth_token.user_account.id):
            return make_response(jsonify({"error": "booking not found"}), 404)
        return booking_schema.jsonify(booking)

    @staticmethod
    @api_bp.route("/bookings/<id>", methods=["DELETE"])
    @auth_token_required()
    def delete_booking(id, auth_token={}):
        '''
        Delete's the perticular booking from the database.

        :param auth_token: The users authentication token to ensure only logged
                           users can access.
        :param id: car_id used to get one single car.

        :return Returns a jsonified data of the booking that was deleted.
        '''
        res = None
        booking = Booking.query.get(id)
        if not booking or auth_token.user_account.id != booking.user_id:
            res = make_response(jsonify(error="booking not found"), 404)
        elif not (booking.active and booking.car.locked):
            res = make_response(jsonify(error="Unauthorized"), 401)
        else:
            res = booking_schema.jsonify(booking)
            booking.delete_booking()
        return res

    @staticmethod
    @api_bp.route('/bookings/<id>', methods=['PATCH'])
    @auth_token_required()
    @load_json()
    @validate_patch({'active', 'end_time', 'calendar_id', 'userface_status'})
    def patch_booking(id, auth_token={}, json_data={}):
        '''
        Set's the fields end_time and active of the booking table in the
        database.

        :param auth_token: The users authentication token to ensure only logged
                           users can access.
        :param id: car_id used to get one single car.
        :param json_data: Json data from the request.

        :return Returns a jsonified car schema with a success message of 200.
        '''
        res = None

        booking = Booking.query.get(id)
        if not booking or booking.user_id != auth_token.user_account.id:
            res = make_response(jsonify(error="booking not found"), 404)
        else:
            booking = Booking.query.get(id)
            for (key, value) in json_data.items():
                if key == 'active':
                    booking.set_active(value)
                elif key == 'end_time':
                    booking.set_endtime(value)
                elif key == 'calendar_id':
                    booking.set_calendarid(value)
                elif key == 'userface_status':
                    booking.set_userface_status(value)
            res = make_response(booking_schema.jsonify(booking), 200)

        return res


class ReportApi:
    @staticmethod
    @api_bp.route('/reports/car/<car_id>', methods=['POST'])
    @auth_token_required(["A"])
    @load_json('description')
    def new_car_report(car_id, json_data={}, auth_token={}):
        description = json_data['description']
        res = None
        new_report = CarReport.create_report({
            'description':
            description,
            'car_id':
            car_id,
            'date_created':
            str(datetime.now()),
            'resolved':
            False
        })
        res = make_response(car_report_schema.jsonify(new_report), 201)
        return res

    @staticmethod
    @api_bp.route('/reports', methods=["GET"])
    @auth_token_required(user_type_required=["E", "A"])
    def get_all_reports(auth_token=None):
        '''
        Gets all the reports from the database

        :param auth_token: The users authentication token to ensure only
            authorised users can access sensitive report data.

        :returns all the reports in json format.
        '''

        cars = Car.query.filter(Car.reports.any()).all()
        report_res = cars_schema.dump(cars)
        for (md, js) in zip(cars, report_res):
            js['reports'] = car_reports_schema.dump(md.reports)
        return jsonify(report_res)

    @staticmethod
    @api_bp.route('/cars/<car_id>/reports/<report_id>', methods=['GET'])
    @auth_token_required(["E"])
    def get_car_report(car_id, report_id, auth_token={}):
        res = None
        report = CarReport.query.get(report_id)
        if report:
            res = car_report_schema.jsonify(report)
        else:
            res = make_response(jsonify(error="report not found"), 404)
        return res

    @staticmethod
    @api_bp.route('/cars/<car_id>/report/<report_id>', methods=["PATCH"])
    @auth_token_required(["E"])
    @load_json()
    @validate_patch({'resolved'})
    def patch_car_report(
        car_id,
        report_id,
        auth_token={},
        json_data={},
    ):
        res = None
        report = CarReport.query.get(report_id)
        if report:
            for (key, value) in json_data.items():
                if key == 'resolved':
                    report.update_report_status(value)
            res = car_report_schema.jsonify(report)
        else:
            res = make_response(jsonify(error="report not found"), 404)
        return res


class UsersApi:
    @staticmethod
    @api_bp.route("/users", methods=["GET"])
    @auth_token_required(user_type_required=["A"])
    @load_query_params
    def get_all_users(auth_token=None, query_params={}):
        '''
        Gets all the users that are currently in the database.

        :param auth_token: The users authentication token to ensure only logged
                           users can access.
        :param query_params: Used to search the data

        :return Returns the list of users in json format.
        '''
        res = None
        if query_params.get("search_data"):
            fields = {
                "id": db.session.query(User.id).distinct().all(),
                "username": db.session.query(User.username).distinct().all(),
                "firstname": db.session.query(User.firstname).distinct().all(),
                "lastname": db.session.query(User.lastname).distinct().all(),
                "userType": db.session.query(User.userType).distinct().all(),
                "email": db.session.query(User.email).distinct().all(),
            }
            res = jsonify(fields)
        else:
            if query_params:
                filter = ["", "on", "submit"]
                query_params = {
                    k: [x for x in v if x not in filter]
                    for (k, v) in query_params.to_dict(flat=False).items()
                    if k not in filter
                }
            users = User.search(query_params)
            res = users_schema.jsonify(users)
        return res

    @staticmethod
    @api_bp.route("/users/<id>", methods=["GET"])
    @auth_token_required(["A"])
    def get_user(id, auth_token=None):
        '''
        Gets one single user from the database

        :param auth_token: The users authentication token to ensure only
            authorised admins can access sensitive user data.
        :param id: user_id used to get one single user

        :returns the one single user in json format.
        '''
        user = User.query.get(id)
        return user_schema.jsonify(user)

    @staticmethod
    @api_bp.route('/users/<id>', methods=['PATCH'])
    @auth_token_required(["A"])
    @load_json()
    @validate_patch({
        'username', 'firstname', 'lastname', 'userType', 'email', 'pushbullet',
        'br_address'
    })
    def patch_user(id, auth_token={}, json_data={}):
        '''
        Updates the attributes of the user in the database

        :param auth_token: The users authentication token to ensure only logged
                           admins can access.
        :param id: user_id used to get one single user.
        :param json_data: Json data from the request.

        :return Returns a jsonified user schema with a success message of 200
        '''
        res = None
        user = User.query.get(id)
        if not user:
            res = make_response(jsonify(error="user not found"), 404)
        else:
            errors = []
            for (key, value) in json_data.items():
                # TODO look up actively booked car and send to car
                try:
                    user.set_field(key, value, commit=False)
                except Exception as e:
                    errors.append(str(e))
            if errors:
                res = make_response(jsonify(error=errors), 400)
            else:
                try:
                    user.commit_changes()
                    res = make_response(user_schema.jsonify(user), 200)
                except Exception as e:
                    res = make_response(jsonify(error=str(e)), 400)
        return res


class VoiceApi:
    @staticmethod
    @api_bp.route('/voice', methods=['GET'])
    @auth_token_required(["A"])
    def voice_search(auth_token={}):
        res = None
        try:
            res = MasterClient(
                master_ip=MASTERSERVICE_IP()).VoiceRecognitionQuery()
            res = jsonify(message=res.message, status=res.status)
        except Exception as e:
            res = make_response(
                jsonify(error="Could not reach voice service",
                        exception=str(e)), 500)
        return res

    @staticmethod
    @api_bp.route('/voice/ping', methods=['GET'])
    @auth_token_required(["A"])
    def voice_available(auth_token={}):
        return make_response(jsonify(data="success"), 200)


class BluetoothApi:
    @staticmethod
    @api_bp.route('/bluetooth/search', methods=["GET"])
    @auth_token_required(["E"])
    def search(auth_token={}):
        res = None
        try:
            res = []
            search = MasterClient(
                master_ip=MASTERSERVICE_IP()).SearchBluetooth()
            for device in search.results:
                res.append({
                    'bd_addr': device.bd_addr,
                    'device_name': device.device_name
                })

            res = jsonify(res)
        except Exception as e:
            res = make_response(
                jsonify(error="Could not reach bluetooth search service",
                        exception=str(e)), 500)
        return res
