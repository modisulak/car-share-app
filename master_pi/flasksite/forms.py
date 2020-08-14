from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     DateTimeField, FloatField, IntegerField, TextAreaField)
from wtforms.validators import (DataRequired, Length, Email, EqualTo,
                                NumberRange)

from flask_wtf.file import FileField
'''
Register Forms
Using Flask_WT Forms to setup a form that the user can register with
'''

from marshmallow_validators.wtforms import from_wtforms


class Validators:
    username = [DataRequired(), Length(min=3, max=20)]
    email = [DataRequired(), Email(), Length(min=1, max=254)]
    password = [DataRequired(), Length(min=3, max=128)]
    confirmPassword = [DataRequired(), EqualTo('password')]
    firstname = [DataRequired(), Length(min=1, max=50)]
    lastname = [DataRequired(), Length(min=1, max=50)]
    datetime = []
    make = [DataRequired(), Length(min=1, max=50)]
    body_type = [DataRequired(), Length(min=1, max=50)]
    colour = [DataRequired(), Length(min=1, max=50)]
    userType = [DataRequired(), Length(min=1, max=1)]
    seats = [
        DataRequired(),
        NumberRange(min=1, max=7, message="Number of seats between 1 and 7")
    ]
    cost = [DataRequired(), NumberRange(min=15, max=100)]
    lat = [DataRequired()]
    lng = [DataRequired()]
    report = [DataRequired(), Length(min=1, max=255)]
    pushbullet = [DataRequired(), Length(min=1, max=64)]
    br_address = [DataRequired(), Length(min=1, max=64)]


class MaValidators:
    def __init__(self):
        fields = [field for field in dir(Validators) if "__" not in field]
        for field in fields:
            setattr(self, field, from_wtforms(getattr(Validators, field)))


class RegisterForm(FlaskForm):
    '''
    Register Forms
    Using Flask_WT Forms to setup a form that the user can register with
    '''
    # Ensures username is between 3-20 characters, ie. validation
    username = StringField('Username', validators=Validators.username)
    # Ensures that input is an email
    email = StringField('Email', validators=Validators.email)
    password = PasswordField('Password', validators=Validators.password)
    # Ensures that input exists
    confirmPassword = PasswordField('Confirm Password',
                                    validators=Validators.confirmPassword)
    # Ensures that input exists
    firstname = StringField('First Name', validators=Validators.firstname)
    lastname = StringField('Last Name', validators=Validators.lastname)
    submit = SubmitField('Register')  # Register Button to be handled


class LoginForm(FlaskForm):
    '''
    Login Forms
    Using Flask_WT Forms to setup a form that the user can login with
    '''
    username = StringField(
    )  # Ensures username is between 3-20 characters, ie. validation
    password = PasswordField(
        'Password',
        validators=Validators.password)  # Ensures that input exists
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')  # Login button to be handled


class BookingForm(FlaskForm):
    end_time = DateTimeField('End Time',
                             validators=Validators.datetime,
                             format='%m/%d/%Y')
    submit = SubmitField('Confirm Booking')  # Book car button


class CarSearchForm(FlaskForm):
    '''
    Search Bar
    This is a search bar that allows users to look for specific cars
    in the database
    '''
    submit = SubmitField('Search')


class FaceVideoUploadForm(FlaskForm):
    file = FileField("Record")
    submit = SubmitField('Done')


class UnlockcarForm(FlaskForm):
    submit_unlock = SubmitField("Unlock car")


class CancelbookingForm(FlaskForm):
    submit_cancel = SubmitField("Cancel booking")


class ReturncarForm(FlaskForm):
    submit_return = SubmitField("Return Car")


class Enablefaceunlock(FlaskForm):
    submit_enablefaceunlock = SubmitField("Enable face Unlock")


class Disablefaceunlock(FlaskForm):
    submit_disablefaceunlock = SubmitField("Disable face Unlock")


# TODO: Add Validators
class EditCarForm(FlaskForm):
    '''
    Edit Car Form
    Using Flask_WT Forms to setup a form that the admin can use to
    update car information.
    '''
    make = StringField('Car Make: ', validators=Validators.make)
    body_type = StringField('Car Model: ', validators=Validators.body_type)
    colour = StringField('Car Colour: ', validators=Validators.colour)
    seats = IntegerField('Car Seats: ', validators=Validators.seats)
    cost = FloatField('Car CostPerHour: ', validators=Validators.cost)
    lat = FloatField('Car Lat: ', validators=Validators.lat)
    lng = FloatField('Car Lng: ', validators=Validators.lng)
    submit = SubmitField('Update')


class ReportCarForm(FlaskForm):
    '''
    Report Car Form
    Using Flask_WT Forms to setup a form that the admin can use to
    reports car's with faults.
    '''
    report = TextAreaField('Report: ', validators=Validators.report)
    submit = SubmitField('Report')


class UserSearchForm(FlaskForm):
    '''
    Search Bar
    This is a search bar that allows admins to look for specific users
    in the database
    '''
    submit = SubmitField('Search')


class EditUserForm(FlaskForm):
    '''
    Edit User Form
    Using Flask_WT Forms to setup a form that the admin can use to
    update user information.
    '''
    username = StringField('User Name: ', validators=Validators.username)
    firstname = StringField('First Name: ', validators=Validators.firstname)
    lastname = StringField('Last Name: ', validators=Validators.lastname)
    userType = StringField('User Type: ', validators=Validators.userType)
    email = StringField('Email: ', validators=Validators.email)
    pushbullet = StringField('Pushbullet: ', validators=Validators.pushbullet)
    br_address = StringField('Bluetooth Address: ',
                             validators=Validators.br_address)
    submit = SubmitField('Update')
