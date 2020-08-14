# credit to https://flask.palletsprojects.com/en/1.1.x/tutorial/
import click
from flask import current_app
from flask.cli import with_appcontext
from .models import db
from .populate import populate_db


def init_db():
    """Execute deletion of existing tables and recreation of tables in MySQL
    DB"""
    with current_app.app_context():
        db.drop_all()
        db.create_all()
        db.session.commit()


def populatedb():
    """Populating data in MySQL DB"""
    with current_app.app_context():
        init_db()
        populate_db()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Create CLI command `init-db` to clear the existing data and create new
    tables."""
    init_db()
    click.echo('Initialized the database.')


@click.command('populate-db')
@with_appcontext
def populate_db_command():
    """Create CLI command `populate-db` to """
    populatedb()
    click.echo('Initialized and populated the database.')


def init_app(app):
    with app.app_context():
        db.init_app(app)
        app.cli.add_command(init_db_command)
        app.cli.add_command(populate_db_command)
