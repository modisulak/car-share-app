import os
from master_pi.utils import get_sqlalchemy_config


class __GithubTestingConfig:
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = '8096fca8544fc48d3cf7767a43f61fe5'
    DATABASE = {
        'database': 'test_db',
        'host': '127.0.0.1',
        'user': 'root',
        'password': 'password',
        'port': ":" + os.environ.get('DB_PORT')
    }
    PASSWORD_HASHING_METHOD = "plain"


UseGithubTestingConfig = get_sqlalchemy_config(__GithubTestingConfig)
