def test_admin_edit_user(client, auth, app):
    # "U" login unauthorized
    auth.login()
    res = client.get("/users/1/edit")
    assert res.status_code != 200
    res = client.post("/users/1/edit", data="abc123")
    assert res.status_code != 200
    auth.login_api()
    res = auth.api.patch("api/users/1", json={"abc123": 0})
    assert res.status_code == 401

    # "A" login authorized
    auth.login(username="bmooreed", password="bmooreed")
    auth.login_api(username="bmooreed", password="bmooreed")
    data = {
        "username": "bingbong",
        "firstname": "bing",
        "lastname": "bong",
        "userType": "A",
        "email": "bing@bong.com"
    }
    res = auth.api.patch("api/users/1", json=data)
    assert res.status_code == 200
    api_data = res.get_json()
    assert all(api_data[k] == v for (k, v) in data.items())


def test_admin_add_car(auth, client):
    # "U" user unauthorised
    auth.login()
    res = client.get("cars/new")
    assert res.status_code != 200

    # "A" user authorised
    auth.login(username="bmooreed", password="bmooreed")
    res = client.get("cars/new")
    assert res.status_code == 200

    auth.login_api(username="bmooreed", password="bmooreed")
    data = {
        "make": "bing",
        "body_type": "bong",
        "colour": "bingus",
        "seats": 5,
        "lng": 10.1010,
        "lat": 20.2010,
        "costPerHour": 999.22
    }
    res = auth.api.post("api/cars", json=data)
    assert res.status_code == 200
    api_data = res.get_json()
    assert all(api_data[k] == v for (k, v) in data.items())
    assert res.get_json()["id"] == 1


def test_admin_edit_car(auth, client):
    auth.login()
    res = client.get("cars/1/edit")
    assert res.status_code != 200

    auth.login(username="bmooreed", password="bmooreed")
    res = client.get("cars/1/edit")
    assert res.status_code == 200
    auth.login_api(username="bmooreed", password="bmooreed")
    data = {
        "make": "bing",
        "body_type": "bong",
        "colour": "bingus",
        "seats": 5,
        "lng": 10.1010,
        "lat": 20.2010,
        "costPerHour": 999.22
    }
    res = auth.api.patch("cars/1", json=data)
    assert res.status_code == 200


def test_admin_report_car(auth, client):
    auth.login()
    res = client.get("cars/1/report")
    assert res.status_code != 200

    auth.login(username="bmooreed", password="bmooreed")
    res = client.get("cars/1/report")
    assert res.status_code == 200
    auth.login_api(username="bmooreed", password="bmooreed")
    data = {"description": "test test 123"}
    res = auth.api.post('api/reports/car/1', json=data)
    assert res.status_code == 201
    api_data = res.get_json()
    assert api_data['description'] == data['description']
    assert api_data['car_id'] == 1
    assert api_data['resolved'] is False
