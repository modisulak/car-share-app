# credit to https://flask.palletsprojects.com/en/1.1.x/tutorial/
# credit to https://hackersandslackers.com/flask-sqlalchemy-database-models/

from flask import Flask, current_app


def create_app(test_config=None):
    """Creation of the Flask Application and the setting of each
    of the site's endpoints.

    :return: App - Returns the application to run
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    if test_config is None:
        from master_pi.instance.config import UseDevelopmentConfig
        # load the instance config, if it exists, when not testing
        app.config.from_object(UseDevelopmentConfig())
    else:
        # load the test config if passed in
        app.config.from_object(test_config())

    from .db import init_app
    init_app(app)

    from .site import index_bp
    app.register_blueprint(index_bp)

    from .site.auth import auth_bp
    app.register_blueprint(auth_bp)

    from .api import api_bp
    app.register_blueprint(api_bp)

    with app.app_context():
        # within this block, current_app points to app.
        print(current_app.name)

    return app
