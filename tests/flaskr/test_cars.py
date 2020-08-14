import simplejson as json
from fnmatch import fnmatch
from urllib.parse import urlencode


# test cars endpoints not accessable when logged out
def test_cars_not_logged_in_site(client):
    res = client.get("/cars")
    assert 302 == res.status_code
    assert res.headers['Location'] == "http://localhost/auth/logout"

    res = client.get("/cars/1")
    assert 302 == res.status_code
    assert res.headers['Location'] == "http://localhost/auth/logout"


# test all_cars
def test_all_cars_site(client, auth):
    auth.login()
    res = client.get('/cars')
    assert 200 == res.status_code
    assert b"Book Car" in res.data


# test one_car, making a booking through form
def test_one_car_site_booking_form(client, auth, datetime_offset,
                                   start_car_service):
    auth.login()
    auth.load_userface()
    res = client.get('/cars/2')
    assert 200 == res.status_code
    _ = start_car_service('2')
    res = client.post('/cars/2',
                      data={
                          'Submit': 'Confirm Booking',
                          'end_time': datetime_offset(days=1)()
                      })
    assert fnmatch(res.headers['Location'], 'http://localhost/bookings/*')


# test Unauthorized for logged out users
def test_unauthorized_car_api(client, auth):
    res = client.get('api/cars', headers={'Authorization': "abc123"})
    assert res.status_code == 401
    res = client.get('api/cars')
    assert res.status_code == 401
    res = client.get('api/cars/1', headers={'Authorization': "abc123"})
    assert res.status_code == 401
    res = client.get('api/cars/1')
    assert res.status_code == 401
    res = client.post('api/bookings',
                      json={'car_id': '1'},
                      headers={'Authorization': "abc123"})
    assert res.status_code == 401
    res = client.post('api/bookings', json={'car_id': '1'})
    assert res.status_code == 401
    res = client.post('api/bookings')
    assert res.status_code == 401


# test get all cars api
def test_get_all_cars_api(client, auth):
    res = auth.login_api()
    res = auth.api.get('api/cars')
    car_data = res.get_json()
    assert len(car_data) >= 20
    from master_pi.flasksite.db.populate import car_keys
    assert all(k in car.keys() for car in car_data for k in car_keys)


# test get a car api
def test_get_car_api(client, auth, datetime_offset):
    res = auth.login_api()
    res = auth.api.get('api/cars')
    car_data = res.get_json()
    for car in car_data:
        res = auth.api.get('api/cars/{}'.format(car['id']))
        assert res.status_code == 200
        res_data = json.loads(res.data)
        res_data['active'] = False
        assert car == res_data


def test_car_map(client, auth):
    auth.login()
    res = client.get('/map')
    assert res.status_code == 200


def test_single_car_map(client, auth):
    auth.login()
    auth.login_api()
    for car in auth.api.get("api/cars").get_json():
        res = client.get("map/car/{}".format(car["id"]))
        assert res.status_code == 200


def test_car_search(client, auth, app):
    auth.login_api()
    query = [("make", "BMW"), ("make", "Volkswagen"), ("colour", "yellow"),
             ('colour', 'Green'), ("order_by", "price_asc")]
    cars = auth.api.get("api/cars?" + urlencode(query))
    assert cars.status_code == 200
    cars = cars.get_json()
    prev_val = 0
    for car in cars:
        assert car['costPerHour'] > prev_val
        prev_val = car['costPerHour']
        assert car['make'] in ['BMW', 'Volkswagen']
        assert car['colour'] in ['Green', 'Yellow']
