Carshare Setup (Windows)
========================

Create Python Virtual Environment
*********************************
The python virtual environment is created so that the programs dependancies are unique for this project, which protects against system-wide installations of packages which can break other programs

.. note:: This assumes that you have installed, and are running **Python 3.8**

``Bash Console:``

.. code-block:: bash

    python -m venv venv
    source venv/Scripts/activate

Setup Initial Configuration
***************************
This initial setup must be done in the top level folder of the project.
This is a key setup that must be done, and is not dependant on github, meaning that files are not included.

Install Packages Required
-------------------------
This will install all the packages required into the python virtual environment

.. code-block:: bash

    pip install -r reqirements.txt

Export Flask Location
---------------------
Sets the run location so that you can use the command ``flask run``. This also sets **developer mode** which enables new changes to take effect immediately

.. code-block:: bash

    export FLASK_APP=master_pi/flasksite >> venv/Scripts/activate
    export FLASK_ENV=development >> venv/Scripts/activate

Define New Configuration
------------------------
Create a **new file** at the location: ``master_pi/instance/config.py``. Copy and paste the following code::
    
    from master_pi.utils import get_sqlalchemy_config


    class __Config:
        DEBUG = False
        TESTING = False
        DATABASE = None
        SECRET_KEY = None


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
            'database': 'carshare',
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

    UseDevelopmentConfig = get_sqlalchemy_config(__GCPConfig)

Connect to The GCP
******************
To connect to the GCP, we must first ensure the database is running and initialized. Complete the following commands:

.. code-block:: bash

    pip install -e .
    flask run

**Immediately** stop the server using ``ctrl-c`` and then run

.. code-block:: bash

    flask init-db

And that is it! You are done! You can now run ``flask run`` to connect and use the app. 

.. warning:: Make sure you use http://localhost:5000/ **not** http://127.0.0.1:5000/ as only localhost works with the Google Calendar API