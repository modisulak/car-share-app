# credit to https://flask.palletsprojects.com/en/1.1.x/tutorial/

from agent_pi.utils import TESTING_ENV
import datetime

import pytest

from master_pi.flasksite import create_app
from master_pi.flasksite.db import populatedb
from master_pi.grpc.masterservice import serve
from agent_pi.agent import run


@pytest.fixture
def execute_app_sql():
    def closure(app):
        with app.app_context():
            populatedb()

    yield closure


@pytest.fixture
def flask_testing_config():
    testing_env = TESTING_ENV()
    config = None
    if testing_env == 'github':
        from github_config import UseGithubTestingConfig
        config = UseGithubTestingConfig
    else:
        from master_pi.instance.config import TEST_ENVIRONMENTS
        config = TEST_ENVIRONMENTS[testing_env]
    yield config


@pytest.fixture
def app(execute_app_sql, flask_testing_config):

    app = create_app(flask_testing_config)
    execute_app_sql(app)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._user = 'nathandrake'
        self._pass = 'nathandrake'
        self._auth_token = None
        self._client = client
        self.api = self.__api__(self)

    def login(self, username='nathandrake', password='nathandrake'):
        self.logout()
        self._user = username
        self._pass = password
        return self._client.post('/auth/login',
                                 data={
                                     'username': username,
                                     'password': password,
                                     'submit': 'Login'
                                 })

    def login_api(self, username='nathandrake', password='nathandrake'):
        self.logout()
        self._user = username
        self._pass = password
        res = self._client.post('api/auth/login',
                                json={
                                    'username': username,
                                    'password': password
                                })
        assert res.status_code == 200
        print(res.get_json())
        self._auth_token = res.get_json()
        return self._auth_token

    def load_userface(self):
        authtoken = self.login_api(username=self._user, password=self._pass)
        from tests.user_face_data import face_encoding_json_str
        return self._client.patch(
            'api/auth/user',
            json={'userFace': face_encoding_json_str},
            headers={'Authorization': authtoken['token']})

    def logout(self):
        return self._client.get('/auth/logout')

    class __api__:
        def __init__(self, auth):
            self.auth = auth

        def __request__(self, req_type, url, json={}):
            return getattr(self.auth._client,
                           req_type)(url,
                                     json=json,
                                     headers={
                                         'Authorization':
                                         self.auth._auth_token['token']
                                     })

        def post(self, url, json=None):
            return self.__request__('post', url, json=json)

        def get(self, url, json={}):
            return self.__request__('get', url, json=json)

        def delete(self, url, json={}):
            return self.__request__('delete', url, json=json)

        def patch(self, url, json={}):
            return self.__request__('patch', url, json=json)


@pytest.fixture
def auth(client):
    return AuthActions(client)


@pytest.fixture
def datetime_offset():
    def new_date(**delta_params):
        dt = datetime.datetime.now() + datetime.timedelta(**delta_params)

        def format_dt(fstr='%m/%d/%Y'):
            return dt.strftime(fstr)

        return format_dt

    return new_date


@pytest.fixture
def start_car_service(flask_testing_config):
    master = serve(flask_testing_config)

    def start_car(car_id):
        from agent_pi.init_db import run as init_db
        init_db()
        car = run(str(car_id), testing=True)
        return (master, car)

    return start_car
