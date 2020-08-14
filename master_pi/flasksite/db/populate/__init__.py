from ..models import Car, User, Booking, UserFaceEncoding, CarReport, RequestLog
from .. import db
from .cars_data import car_keys, car_data
from .users_data import user_keys, user_data

# TODO "In prior to your demo, create 10-20 Cars on your own (e.g., 2 Admins, 4
# Engineers, 6 Users)"

booking_keys = [
    "active", "start_time", "end_time", "car_id", "user_id", "userface_status"
]
bookings = [
    (False, "2020-06-25T00:00:00", "2020-06-26T00:00:00", "1", "1", False),
    (False, "2020-06-25T00:00:00", "2020-05-26T00:00:00", "2", "2", False),
    (False, "2020-06-25T00:00:00", "2020-05-26T00:00:00", "3", "3", False),
    (False, "2020-06-25T00:00:00", "2020-05-26T00:00:00", "4", "4", False),
    (False, "2020-06-26T00:00:01", "2020-06-27T00:00:00", "1", "1", False),
    (False, "2020-06-26T00:00:01", "2020-06-27T00:00:00", "2", "2", False),
    (False, "2020-06-26T00:00:01", "2020-06-27T00:00:00", "3", "3", False),
    (False, "2020-06-26T00:00:01", "2020-06-27T00:00:00", "4", "4", False),
    (False, "2020-06-26T00:00:01", "2020-06-27T00:00:00", "5", "5", False),
    (False, "2020-06-28T00:00:01", "2020-06-29T00:00:00", "3", "3", False),
    (False, "2020-06-28T00:00:01", "2020-06-29T00:00:00", "1", "1", False),
    (False, "2020-06-28T00:00:01", "2020-06-29T00:00:00", "2", "2", False),
    (False, "2020-06-29T00:00:01", "2020-06-30T00:00:00", "1", "1", False),
    (False, "2020-06-29T00:00:01", "2020-06-30T00:00:00", "2", "2", False),
]

userFace_keys = ["encoding", "user_id"]
userFace_data = [("[]", "1")]

car_report_keys = ["description", "car_id", "date_created", "resolved"]
car_reports = [("Report Test", "1", "2020-05-28T00:00", False)]

request_log_keys = ["request_url", "user_id", "date_created"]
request_logs = [("http://127.0.0.1:5000/main", "1", "2020-06-28T00:00"),
                ("http://127.0.0.1:5000/main", "1", "2020-06-29T00:00"),
                ("http://127.0.0.1:5000/main", "1", "2020-06-28T00:00"),
                ("http://127.0.0.1:5000/main", "2", "2020-06-28T00:00"),
                ("http://127.0.0.1:5000/main", "3", "2020-06-28T00:00"),
                ("http://127.0.0.1:5000/main", "4", "2020-06-28T00:00"),
                ("http://127.0.0.1:5000/main", "1", "2020-06-27T00:00"),
                ("http://127.0.0.1:5000/main", "2", "2020-06-27T00:00"),
                ("http://127.0.0.1:5000/main", "3", "2020-06-27T00:00"),
                ("http://127.0.0.1:5000/main", "4", "2020-06-27T00:00"),
                ("http://127.0.0.1:5000/main", "1", "2020-06-26T00:00"),
                ("http://127.0.0.1:5000/main", "2", "2020-06-26T00:00"),
                ("http://127.0.0.1:5000/main", "3", "2020-06-26T00:00"),
                ("http://127.0.0.1:5000/main", "4", "2020-06-26T00:00"),
                ("http://127.0.0.1:5000/main", "1", "2020-06-30T00:00"),
                ("http://127.0.0.1:5000/main", "2", "2020-06-30T00:00"),
                ("http://127.0.0.1:5000/main", "3", "2020-06-30T00:00"),
                ("http://127.0.0.1:5000/main", "4", "2020-06-30T00:00")]


def populate_db():
    for user in user_data:
        user_dict = {}
        for (index, key) in enumerate(user_keys):
            user_dict[key] = user[index]
        new_user = User.create_user(user_dict, commit=False)
        print("adding {}".format(user))
        db.session.add(new_user)

    for uf in userFace_data:
        face_dict = {}
        for (index, key) in enumerate(userFace_keys):
            face_dict[key] = uf[index]
        new_userFace = UserFaceEncoding(**face_dict)
        db.session.add(new_userFace)

    for car in car_data:
        car_dict = {}
        for (index, key) in enumerate(car_keys):
            car_dict[key] = car[index]
        new_car = Car(**car_dict)
        print("adding {}".format(car))
        db.session.add(new_car)

    for booking in bookings:
        booking_dict = {
            key: booking[index]
            for (index, key) in enumerate(booking_keys)
        }
        new_booking = Booking(**booking_dict)
        print("adding {}".format(booking))
        db.session.add(new_booking)

    db.session.commit()

    for car_report in car_reports:
        report_dict = {
            key: car_report[index]
            for (index, key) in enumerate(car_report_keys)
        }
        new_report = CarReport(**report_dict)
        print("adding {}".format(car_report))
        db.session.add(new_report)

    for request_log in request_logs:
        request_dict = {
            key: request_log[index]
            for (index, key) in enumerate(request_log_keys)
        }
        new_request = RequestLog(**request_dict)
        print("adding {}".format(request_dict))
        db.session.add(new_request)

    db.session.commit()
