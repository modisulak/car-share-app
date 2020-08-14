import pytest
from flask import g, session
import uuid
from master_pi.flasksite.db.models import User


def test_register_page_status(client):
    assert client.get('/auth/register').status_code == 200


def test_register_api(client, app):
    res = client.post('/auth/register',
                      data={
                          'email': 'a@a.co',
                          'username': 'aaa',
                          'password': 'aaa',
                          'firstname': 'aaa',
                          'lastname': 'aaa',
                          'confirmPassword': 'aaa',
                          'submit': 'Register'
                      })
    assert res.headers['Location'] == 'http://localhost/auth/login'

    with app.app_context():
        user = User.query.filter_by(username='aaa').first()
        assert user is not None

    res = client.post('api/auth/register',
                      json={
                          'email': 'b@b.co',
                          'username': 'bbb',
                          'password': 'bbb',
                          'firstname': 'Nathan',
                          'lastname': 'Drake',
                      })
    json = res.get_json()
    assert json['username'] == 'bbb'


@pytest.mark.parametrize(
    ('username', 'password', 'email', 'firstname', 'lastname', 'message',
     'api_msg'),
    (('', '', '', '', '', b'This field is required.',
      b"This field is required."),
     ('aaa', '', '', '', '', b'This field is required.',
      b"This field is required."),
     ('aa', '', '', '', '', b'Field must be between 3 and 20 characters long.',
      b"This field is required."),
     ('aaa', 'aaa', 'a', '', '', b'Invalid email address.',
      b"This field is required."),
     ('aaa', 'aaa', 'aaa', 'aaa', 'aaa', b'Invalid email address.',
      b"Not a valid email address."),
     ('aaa', 'aaa', 'a@a.com', 'aaa', '', b'This field is required',
      b'This field is required'),
     ('nathandrake', 'nathandrake', 't@t.com', 'nathan', 'drake',
      b'username taken', b'username taken')))
def test_register_validate_input(client, username, password, email, firstname,
                                 lastname, message, api_msg):
    response = client.post('/auth/register',
                           data={
                               'username': username,
                               'password': password,
                               'confirmPassword': password,
                               'email': email,
                               'firstname': firstname,
                               'lastname': lastname,
                               'submit': 'Register'
                           })
    assert message in response.data

    response = client.post('api/auth/register',
                           json={
                               'username': username,
                               'password': password,
                               'email': email,
                               'firstname': firstname,
                               'lastname': lastname,
                           })
    assert api_msg in response.data


@pytest.mark.parametrize(('json_data', 'api_msg'), (({
    'username': 'test'
}, b'malformed request'), ({
    'password': 'test'
}, b'malformed request'), ({}, b'malformed request'), ({
    'username': None,
    'password': None
}, b'Field may not be null.')))
def test_register_api_malformed_request(client, json_data, api_msg):
    response = client.post('api/auth/login', json=json_data)
    assert api_msg in response.data


def test_login_page_status(client):
    assert client.get('/auth/login').status_code == 200


def test_login_api(client, auth):
    res = auth.login()
    assert res.headers['Location'] == 'http://localhost/'

    with client:
        client.get('/')
        assert session['user_id'] == '1'
        assert g.user.username == 'nathandrake'
        assert uuid.UUID(g.auth_token)

    res = client.post('api/auth/login',
                      json={
                          'username': 'nathandrake',
                          'password': 'nathandrake'
                      })
    json = res.get_json()
    assert json['user_id'] == 1
    assert uuid.UUID(json['token'])


def test_login_register_pipeline(client, auth):
    # test full register -> login pipeline

    user = str(uuid.uuid4()).split("-")[0]

    res = client.post('/auth/register',
                      data={
                          'email': '{0}@{0}.co'.format(user),
                          'username': user,
                          'password': user,
                          'firstname': user,
                          'lastname': user,
                          'confirmPassword': user,
                          'submit': 'Register'
                      })
    assert res.headers['Location'] == 'http://localhost/auth/login'

    res = client.post('/auth/login', data={'username': user, 'password': user})

    res = auth.login(user, user)
    assert res.headers['Location'] == 'http://localhost/'

    res = client.get('/cars')

    assert bytes(user, 'utf-8') in res.data


@pytest.mark.parametrize(
    ('username', 'password', 'message', 'api_msg'),
    (('a', 'test', b'Field must be between 3 and 20 characters long.',
      b'Field must be between 3 and 20 characters long.'),
     ('abc', 'test', b'Incorrect login information.',
      b'Incorrect login information.'),
     ('test', 'a', b'Field must be between 3 and 128 characters long.',
      b"Incorrect login information.")))
def test_login_validate_input(auth, client, username, password, message,
                              api_msg):
    response = auth.login(username, password)
    assert message in response.data

    response = client.post('api/auth/login',
                           json={
                               'username': username,
                               'password': password
                           })
    assert api_msg in response.data


@pytest.mark.parametrize(('json_data', 'api_msg'), (({
    'username': 'test'
}, b'malformed request'), ({
    'password': 'test'
}, b'malformed request'), ({}, b'malformed request'), ({
    'username': None,
    'password': None
}, b'Field may not be null.')))
def test_login_api_malformed_request(client, json_data, api_msg):
    response = client.post('api/auth/login', json=json_data)
    assert api_msg in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session
        assert g.user is None


def test_user_face_api(client, auth, app):
    authtoken = auth.login_api()
    from tests.user_face_data import face_encoding_json_str
    res = client.patch('api/auth/user',
                       json={'userFace': face_encoding_json_str},
                       headers={'Authorization': authtoken['token']})
    assert "OK" in res.status
    from facial_recognition import FaceEncoding
    with app.app_context():
        user = User.query.get(authtoken['user_id'])
        encoding_str = user.userFace[0].encoding
        numpy_array = FaceEncoding.from_json_str(encoding_str)
        assert len(numpy_array) > 0


def test_redirect_face_upload_encode(client, auth):
    auth.login('adoog', 'adoog')

    # redirect to upload if no user face file
    res = client.get('auth/face_encode')
    assert res.headers['Location'] == 'http://localhost/auth/face_upload'

    # redirect to home if user already has face model encoding
    # test loading user face model through users/{} patch API
    res = auth.load_userface()
    # try accessing face_encode site endpoint
    res = client.get('auth/face_encode')
    assert res.headers['Location'] == 'http://localhost/'
    res = client.get('auth/face_upload')
    assert res.headers['Location'] == 'http://localhost/'
