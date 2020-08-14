# car-share

## **RMIT PIoT Course Assignment 2: IoT CarShare Project**

## The Team
* Moditha Sulakshana (me)
* Jack-Hollis-London - [GitHub](https://github.com/jh0l)

## Run the Master-Pi Flask Server

#### Install MySQL database server

https://dev.mysql.com/downloads/mysql/

#### Create python3 Virtual Environment

_while at the root of car-share repo_

```bash
pwd
.../car-share
pip3 install --upgrade pip
python3 -m venv venv
source venv/bin/activate
```

#### Install Packages From `requirements.txt`

_while still in venv at root of car-share repo_

```bash
pip install -r requirements.txt
```

_Note:_ Installation may crash while downloading all the requirements. This is
okay, run the install command again, it will start off loading cached downloads,
then download some more. Keep restarting the installation until it successfully
installs and exits without errors.

#### Export Flask Environment Variables

```bash
# FLASK_APP is the location of the flask app relative to the root of the car-share repository -
echo export FLASK_APP=master_pi/flasksite >> venv/bin/activate
# This will enable development mode
echo export FLASK_ENV=development >> venv/bin/activate
# activate venv with new export settings
source venv/bin/activate
```

#### Define `master_pi/instance/config.py`

The configuration in this file contains data you as a developer may want to keep
secret, such as database passwords and the app's secret key used for encrypting
sessions, passwords, and cookies etc. Your configuration will look something
like this if your MySQL database is running on your machine and can be accessed
by localhost. You may or may not have a password depending on whether you've set
a password on your MySQL database. The Oracle MySQL installer will let you set a
password.

#### If Using GCP instead of a local MySQL db, you need another config. You will need to change what Configuration is imported in `master_pi/flasksite/__init__.py`.

_`master_pi/instance/config.py`_

```python
from master_pi.utils import get_sqlalchemy_config


class __Config:
    DEBUG = False
    TESTING = False
    DATABASE = None
    SECRET_KEY = None
    PASSWORD_HASHING_METHOD = "pbkdf2:sha256"


# This is the config we are using
class _DevelopmentConfig(__Config):
    DEBUG = True
    SECRET_KEY = '8096fca8544fc48d3cf7767a43f61fe5'
    DATABASE = {
        'host': 'localhost',
        'database': 'css_db',
        'user': 'root',
        'password': 'password',
    }

class __RaspberryTestingConfig(_DevelopmentConfig):
    TESTING = True
    DATABASE = {
        'host': '192.168.0.62',
        'database': 'test_db',
        'user': 'username',
        'password': 'password',
    }

class __TestingConfig():
    WTF_CSRF_ENABLED = False  # enable in production
    TESTING = True
    PASSWORD_HASHING_METHOD = "plain"


class __DevelopmentTestingConfig(__TestingConfig, _DevelopmentConfig):
    def __init__(self):
        _DevelopmentConfig.DATABASE.update({'database': 'test_db'})


# For testing inside docker
class _DockerTestingConfig(__DevelopmentTestingConfig):
    DATABASE = {
        'host': 'host.docker.internal',  # docker host localhost proxy
        'database': 'test_db',
        'user': 'root',
        'password': 'password',
    }


class __GCPConfig(_DevelopmentConfig):
    # GCP database parameters
    DATABASE = {
        'host': '35.201.14.253',
        'database': 'test_db',
        'user': 'rootest',
        'password': '@Rootpass420',
    }


class __GCPTestingConfig(__TestingConfig, __GCPConfig):
    pass


TEST_ENVIRONMENTS = {
    "docker": get_sqlalchemy_config(_DockerTestingConfig),
    "native": get_sqlalchemy_config(__DevelopmentTestingConfig),
    "GCP": get_sqlalchemy_config(__GCPTestingConfig),
}

UseDevelopmentConfig = get_sqlalchemy_config(_DevelopmentConfig)

```

### **To connect to GCP database requires a different config**

#### Install the car-share Repository

```bash
pip install -e .
```

#### Initialise DB and Run the Server

First you need to run the flask server to register the `populate-db` command
with flask, then exit out of the server, run the `populate-db` command, now you
can run the flask server again with the database ready.

```bash
flask run
ctrl-c # or however you stop the flask server
flask populate-db
flask run
```

#### Enabling Facial Recognition

In order for facial recognition to work, the python packages imutils an cv2 need
to be installed. These packages are not installed by default. If you have set up
these packages on your device, you can enable facial recognition by setting the
environment variables `FACE_RECOG=ENABLED`, `IS_PI=True`, `ENABLE_SOCKETS=True`:

```bash
export FACE_RECOG=ENABLED
export IS_PI=True
export ENABLE_SOCKETS=True
```

Or enable it automatically when entering virtual environment

```bash
echo export FACE_RECOG=ENABLED >> venv/bin/activate
echo export IS_PI=True >> venv/bin/activate
echo export ENABLE_SOCKETS=True >> venv/bin/activate
```

Secondly, the repository's python virtual envorinment can only access cv2 and
friends if the venv has access to system site packages. To check this, open
venv/pyvenv.cfg. Make sure `include-system-site-packages = true` like this:

```properties
home = /usr/bin
include-system-site-packages = true
version = 3.5.3
```

If you've had to change this from false to true, you will need to exit and
reenter the venv for the changes to take effect. To make sure it has worked,
try:

```bash
(venv) $ python3
import cv2
```

Thirdly, make sure the "haarcascade_frontalface_default.xml" classifier file is
present in the instance directory at the of the repository. The instance folder
will be created by the facial recognition module the first time it is run. An
Exception will be raised giving the address of where the
""haarcascade_frontalface_default.xml" should be located.

#### Installing Bluetooth packages on Raspberry Pi

As linux packes need to be installed manually, so does the bluetooth python
package

```bash

sudo apt install libbluetooth-dev bluetooth bluez python-bluez blueman
pip3 install pybluez
```

Once these pacackages are installed, bluetooth can be enabled with env var
ENABLE_BLUETOOTH

```bash
export ENABLE_BLUETOOTH=True
```

#### Deploy Flask Server With Waitress

To be able to access the flask site from beyond your own computer, you can use
`waitress` as python wysgi web server. Using waitress on a raspberry pi, the
flask site can be accessed from your local area network at
[http://raspberrypi.modem:8080](http://raspberrypi.modem:8080)

```bash
pip install waitress
waitress-serve --call 'master_pi.flasksite:create_app'
```

### Generate gRPC server and client code

If you are not already, go to the root directory of the project. Once there, run
this command to generate the gRPC pb2 and pb2_grpc python code.

```bash
python3 -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/css_rpc/*.proto
```

The grpc modules can now be imported.

If a change is made to a proto file, you will need to generate the pb2 and
pb2_grpc python code again to see the changes in the system.

### Installing QR Code service requirements

Using QR Code service requires installing `pyzbar` package, this is only
available on configurations specifically have support for it.

```bash
pip install pyzbar
```

### Running servers

In order for flasksite to make requests to a car socket service, the env var
`ENABLE_SOCKETS` is to be enabled. If you have already added env vars to enable
facial recognition, `ENABLE_SOCKETS` will be included already.

```bash
export ENABLE_SOCKETS=True
```

add global python packages to venv via
`venv/pyvenv.cfg/include-system-site-packages = True`

set environment variables according to participating machines' properties

start `waitress-serve` of `flasksite`

start `masterservice.py`

start `agent.py` service for each car being used

#### Troubleshooting

If when you try to import from the css_rpc module, python cannot find the
css_rpc module, you may need to reinstall the project so that python knows where
to look for the css_rpc module.

```bash
pip install -e .
```

# Testing Suite

_Testing Suite credit to
https://github.com/coding-geographies/dockerized-pytest-course_

### Prerequisites

**Install Docker (Optional, pytest can from venv)**

-   These tests have been packaged to run with all dependencies installed within
    a Docker container. The Docker image is based on python 3.5-slim

**To run open a shell**

```bash

docker-compose build
docker-compose run test bash
```

**This will open the docker shell and you can run one of the following
commands:**

### Specifying database for Testing

Before running tests you need to make sure your tests are using the right
database. By default, tests will run on GCP. If you have a local database, tests
will run faster. To switch, export the environment variable `TESTING_ENV`:

```bash
export TESTING_ENV=native
```

_change back_

```bash
export TESTING_ENV=GCP
```

### Configuring environment variables for testing

To enable testing GRPC socket services, configure the following environment
variables

````bash
SOCKETS_ENABLED=True
LAN_IP=127.0.0.1

### Running Tests

_Run the entire test suite_

```bash
pytest
````

_Run the tests for a certain test or file matching a keyword_

```bash
pytest -k <test_file_name>
```

_Run tests while printing all variables and verbose output_

```bash
pytest -vvl
```

_Create coverage report html file for certain modules_

```bash
pytest --cov --cov-report=html master_pi/ agent_pi/ tests/ facial_recognition/
```

_Stop pytest from capturing stdout_

```bash
pytest --capture=no
```

_Stop testing the first time a test is failed_

```bash
pytest -x
```

**To exit the shell**

```bash
exit
```

### Debugging

If you'd like to debug a piece of code, you can add the following built-in
function to a section of the code to enter into the pdb debugger while running
pytest. - `breakpoint()` - This is useful for getting initial test output
