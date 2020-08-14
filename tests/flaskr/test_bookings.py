# test book car api
import simplejson as json
from master_pi.flasksite.db.models import Car


def test_history(client, auth):
    res = client.get('/history')
    assert res.status_code == 302
    auth.login()
    res = client.get("/history")
    assert res.status_code == 200


def test_one_booking(client, auth):
    auth.login()
    # see booking for nathandrake from populated_data
    res = client.get("/bookings/1")
    assert res.status_code == 200

    # adoog cannot see same booking
    auth.logout()
    auth.login(username="adoog", password="adoog")
    res = client.get("bookings/1")
    assert res.status_code == 302

    # adoog cannot see non existant booking
    res = client.get("bookings/534")
    assert res.status_code == 302


def test_car_booking_creation_api(client, auth, app, datetime_offset,
                                  start_car_service):

    res = auth.login_api(username='adoog', password='adoog')
    res = auth.api.get('api/cars')
    car_data = json.loads(res.data)
    car = car_data[0]
    # keep grpc servers in scope to prevent servers stopping
    _ = start_car_service(car['id'])
    res = auth.api.post('api/bookings',
                        json={
                            'car_id':
                            car['id'],
                            'end_time':
                            datetime_offset(days=1)('%Y-%m-%d %H:%M:%S')
                        })
    assert res.get_json(
    )["error"] == "facial recognition is required to make a booking"
    auth.load_userface()
    created_booking_res = auth.api.post(
        'api/bookings',
        json={
            'car_id': car['id'],
            'end_time': datetime_offset(days=1)('%Y-%m-%d %H:%M:%S')
        })
    assert "CREATED" in created_booking_res.status
    res = auth.api.post('api/bookings',
                        json={
                            'car_id':
                            car['id'],
                            'end_time':
                            datetime_offset(days=1)('%Y-%m-%d %H:%M:%S')
                        })
    assert res.get_json()["error"] == "car is not available"
    res = auth.api.post('api/bookings',
                        json={
                            'car_id':
                            car_data[1]['id'],
                            'end_time':
                            datetime_offset(days=1)('%Y-%m-%d %H:%M:%S')
                        })
    assert res.get_json(
    )["error"] == "cannot make a booking while another booking is active"

    # login with nathandrake
    auth.login_api()

    b_id = created_booking_res.get_json()['id']

    # cannot cancel a booking if unauthorised (adoog vs nathandrake)
    res = auth.api.delete("api/bookings/{}".format(b_id))
    assert res.status_code == 404

    # cannot unlock a car if unauthorised
    res = auth.api.patch('api/cars/{}'.format(car['id']),
                         json={'locked': False})
    assert res.status_code == 401

    # login as adoog
    auth.login_api(username="adoog", password="adoog")
    # car is not yet unlocked, cancelling booking is allowed
    res = auth.api.delete('api/bookings/{}'.format(b_id))
    assert res.status_code == 200

    # cannot unlock a car if user has no active booking with car
    res = auth.api.patch('api/cars/{}'.format(car['id']),
                         json={'locked': False})
    assert res.status_code == 401

    created_booking_res = auth.api.post(
        'api/bookings',
        json={
            'car_id': car['id'],
            'end_time': datetime_offset(days=1)('%Y-%m-%d %H:%M:%S')
        })

    assert "CREATED" in created_booking_res.status

    # unlocking a car while booking still active is allowed
    res = auth.api.patch('api/cars/{}'.format(car['id']),
                         json={'locked': False})
    assert res.status_code == 200

    # cannot lock car again while booking still active
    res = auth.api.patch('api/cars/{}'.format(car['id']),
                         json={'locked': True})
    assert res.status_code == 400

    # user can deactivate their booking
    b_id = created_booking_res.get_json()['id']
    res = auth.api.patch('api/bookings/{}'.format(b_id),
                         json={'active': False})
    assert res.status_code == 200

    # car has been locked automatically by deactivating booking
    with app.app_context():
        car_updated = Car.query.get(car['id'])
        assert car_updated.locked

    # cannot cancel a booking if booking inactive
    res = auth.api.delete('api/bookings/{}'.format(b_id))
    assert res.status_code == 401


# def test_car_booking_updating(client, auth):
