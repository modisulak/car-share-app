from flask import (Blueprint, render_template, g, flash, redirect, url_for,
                   request, make_response, Markup)
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField
from master_pi.flasksite.site.auth import login_required, restrict_user_type
from master_pi.flasksite.api import (CarsApi, BookingApi, ReportApi, UsersApi,
                                     BluetoothApi, AuthApi)

from master_pi.flasksite.forms import (BookingForm, CarSearchForm,
                                       UnlockcarForm, CancelbookingForm,
                                       ReturncarForm, Enablefaceunlock,
                                       Disablefaceunlock, EditCarForm,
                                       ReportCarForm, UserSearchForm,
                                       EditUserForm)
from master_pi.flasksite.api import load_query_params
import time

index_bp = Blueprint('main', __name__)


@index_bp.route('/')
@login_required
def home():
    '''
    Home Page: The main page lists all the cars that are available

    :return: List of all cars
    :rtype: Function
    '''
    return redirect(url_for('main.all_cars'))


@index_bp.route('/about')
def about():
    """
    About Page:
    This page will show you all about the app
    """
    return render_template('about.html')


@index_bp.route('/history')
@login_required
def history_booking():
    """
    History:
    This page will show you all about all the previous bookings
    of the the current user

    Booking Variable gets Jsonified bookings of all the previous bookigns
    related to the user_id, that isn't active.

    Returns a rendered histroy page.

    """
    bookings = []
    res = BookingApi.get_bookings(query_params={'user_id': g.user.id})
    if "OK" in res.status:
        bookings = res.get_json()
    else:
        flash("{}".format(res.get_json()['error']), "danger")
    if not res.get_json():
        flash("You have no previous bookings", 'info')
    return render_template('history.html', bookings=bookings)


# Nat has written this part no idea what this does?
@index_bp.route('/cars', methods=['GET', 'POST'])
@login_required
def all_cars():
    '''
    Lists the cars that are available, this is sent to the homepage.

    variable cars: A json variable that holds the data from the cars database in
    json form
    varaible r: Gets all cars from the API, and sends them to ``cars`` if **OK**
    optional: a form can be submitted containing filtering options, the query
    parameters from the form will be added to the url then the page will be
    reloaded. The endpoint adds the URL's query parameters to the Car API call's
    query parameters to filter the returned cars
    :type cars: List of type database.model.Car
    :type r: CarsApi

    :return: Returns home.html with the cars data being sent
    :rtype: HTML/CSS

    '''

    form = CarSearchForm()
    if form.is_submitted():
        url = url_for('main.all_cars', **request.form.to_dict(flat=False))
        return redirect(url)

    cars = []
    r = CarsApi.get_all_cars(query_params=request.args)

    if "OK" in r.status:
        cars = r.get_json()
        if len(cars) == 0:
            flash(
                "No options found matching your search, try broadening your\
                    criteria", "primary")
    else:
        flash("{}".format(r.get_json()['error']), 'danger')
    timenow = str(time.time())
    return render_template('home.html', cars=cars, form=form, cachekey=timenow)


@index_bp.route("/cars/<car_id>", methods=["POST", "GET"])
@login_required
def one_car(car_id):
    '''
    Redirects user to the car of their choice to be able to be booked

    :variable form: The booking form that is then sent to the html to be
    displayed
    :variable r: The booking API that enables the car to be booked specifically
    :variable g: Requests the car_id from the database using the api

    :type form: BookingForm
    :type r: BookingApi
    :type g: Object

    :return: Returns booking.html with the cars data being sent,
             as well as the form
    :rtype: HTML/CSS

    '''
    form = BookingForm()

    # cancelbookingform = CancelbookingForm()
    if form.validate_on_submit():
        g.api_request_json = {
            "car_id": car_id,
            "end_time": str(form.end_time.data)
        }
        r = BookingApi.new_booking()
        if "CREATED" in r.status:
            booking = r.get_json()
            return redirect(
                url_for('main.one_booking', booking_id=booking['id']))
        else:
            flash("{}".format(r.get_json()['error']), 'danger')
    data = CarsApi.get_car(car_id).get_json()
    return render_template('cars.html', cars=data, form=form)


@index_bp.route("/add_google_calendar_event_id", methods=["POST"])
@login_required
def add_google_calendar_id():
    """
    Add's the google calender_id to the bookings table in the database
    through the BookingsApi

    json_data variable: contains the Jsonified data of the request being sent.
    booking_id and calender_id: consist of the id's from the jsonified data

    Returns a success response if valid, else returns a error 400 resonse.
    """
    try:
        json_data = request.get_json()
        booking_id = json_data['booking_id']
        calendar_id = json_data['calendar_event_id']
        g.api_request_json = {'calendar_id': calendar_id}
        res = BookingApi.patch_booking(booking_id)
        if "OK" in res.status:
            return make_response("success", 200)
        return make_response("failed", 400)
    except BaseException as e:
        return make_response("error {}".format(e), 400)


class BookingButtonOps:
    supported = {
        "submit_cancel", "submit_unlock", "submit_return",
        "submit_enablefaceunlock", "submit_disablefaceunlock"
    }

    @staticmethod
    def submit_cancel(booking_id):
        # contact api
        res = BookingApi.delete_booking(booking_id)
        if "OK" in res.status:
            flash("Booking Cancelled", "primary")
        else:
            flash("{}".format(res.get_json()['error']), 'danger')

    @staticmethod
    def submit_unlock(booking_id):
        # Updates the car lock status to false when the user unlocks the car.
        booking = BookingApi.get_booking(booking_id).get_json()
        g.api_request_json = {'locked': False}
        res = CarsApi.patch_car(booking['car_id'])
        if "OK" not in res.status:
            flash("{}".format(res.get_json()['error']), 'danger')
        else:
            flash("car unlocked", "success")

    @staticmethod
    def submit_return(booking_id):
        # the state of the car True.
        # set booking active false, add end time to booking, lock car
        # set car locked by deactivating booking
        current_date = datetime.now()
        g.api_request_json = {
            'active': False,
            'end_time': str(current_date),
        }
        res = BookingApi.patch_booking(booking_id)
        if "OK" in res.status:
            flash("Booking Complete", "primary")
        else:
            flash("{}".format(res.get_json()['error']), 'danger')

    @staticmethod
    def submit_enablefaceunlock(booking_id):
        g.api_request_json = {'userface_status': True}
        res = BookingApi.patch_booking(booking_id)
        if "OK" not in res.status:
            flash("{}".format(res.get_json()['error']), 'danger')
        else:
            flash("face unlock enable", "success")

    @staticmethod
    def submit_disablefaceunlock(booking_id):
        g.api_request_json = {'userface_status': False}
        res = BookingApi.patch_booking(booking_id)
        if "OK" not in res.status:
            flash("{}".format(res.get_json()['error']), 'danger')
        else:
            flash("face unlock disable", "success")


@index_bp.route("/bookings/<booking_id>", methods=["POST", "GET"])
@login_required
def one_booking(booking_id):
    """
    Deals with one single booking that a user has made. Buttons are
    displayed on the booking.html page as follows.

    If booking is active and car is locked:
        Display the unlock car button for the user to unlock the car
        Dispay the cancel button for the user
    If booking is active and car is unlocked:
       Display return car button for the user

    :param booking_id: The booking_id is used to identify the perticular
    booking the user is interacting now with.

    :return: Re-directs to the home page with a success flash depending
    on what button the user clicked on, else flashses an error message.

    """
    res = BookingApi.get_booking(booking_id)
    if "OK" not in res.status:
        flash("booking non-existant", "danger")
        return redirect(url_for('main.home'))

    unlockcarform = UnlockcarForm()
    cancelbookingform = CancelbookingForm()
    returncarform = ReturncarForm()
    enablefaceunlock = Enablefaceunlock()
    disablefaceunlock = Disablefaceunlock()

    booking_data = res.get_json()

    if booking_data['active']:
        submitted = [*request.form.keys()]

        for operation in submitted:
            if operation in BookingButtonOps.supported:
                getattr(BookingButtonOps, operation)(booking_id)

    bookingdata = BookingApi.get_booking(booking_id).get_json()
    if bookingdata.get('error'):
        flash("booking non-existant", "danger")
        return redirect(url_for('main.home'))
    cardata = CarsApi.get_car(bookingdata['car_id']).get_json()

    show_google_calender_button = False
    if not bookingdata.get('calendar_id'):
        show_google_calender_button = True

    return render_template(
        'booking.html',
        show_google_calender_button=show_google_calender_button,
        booking=bookingdata,
        car=cardata,
        unlockcarform=unlockcarform,
        cancelbookingform=cancelbookingform,
        returncarform=returncarform,
        enablefaceunlock=enablefaceunlock,
        disablefaceunlock=disablefaceunlock)  # etc


@index_bp.route("/map")
@login_required
def maps():
    '''
    A Map of all the locations of the car, which has been pushed through this
    method

    data: A json variable that holds the data from the cars database in
                json form
    r: Gets all cars from the API, and sends them to ``cars`` if **OK**

    :type data: List
    :type r: CarsApi

    :return: Returns maps.html with the cars data being sent
    :rtype: HTML/CSS

    '''
    data = []
    r = CarsApi.get_all_cars()
    if "OK" in r.status:
        data = r.get_json()
    else:
        flash("{}".format(r.get_json()['error']), 'danger')
    return render_template('maps.html', cars=data)


@index_bp.route("/map/car/<id>")
@login_required
def map_one_car(id):
    '''
    A map location of a single car.

    :param id: car_id used to uniquely identify the car

    :return: Returns a rendered map html page showing the location of the car

    '''
    res = CarsApi.get_car(id)
    if "OK" not in res.status:
        flash("car not found", 'warning')
        return redirect(url_for('main.home'))
    car = res.get_json()
    data = [car]
    return render_template('one_car_map.html', cars=data, car=car)


@index_bp.route("/cars/<car_id>/edit", methods=["POST", "GET"])
@login_required
@restrict_user_type(["A"])
def edit_car(car_id):
    form = EditCarForm()
    if form.validate_on_submit():
        res = CarsApi.patch_car(car_id,
                                json_data={
                                    'make': form.make.data,
                                    'body_type': form.body_type.data,
                                    'colour': form.colour.data,
                                    'seats': form.seats.data,
                                    'costPerHour': form.cost.data,
                                    'lat': form.lat.data,
                                    'lng': form.lng.data
                                })
        if res.status_code == 200:
            flash("Car information updated successfully", "success")
        else:
            flash("Edit request error: {}".format(res.get_json()['error']),
                  'danger')
    else:
        res = CarsApi.get_car(car_id)
        if res.status_code != 200:
            flash("Data request error: {}".format(res.get_json()["error"]),
                  'warning')
            return redirect(url_for('main.home'))

    if form.is_submitted() and not form.validate():
        for (key, value) in form.errors.items():
            flash("Field {}: {}".format(key, value), 'danger')
    data = res.get_json()
    return render_template('edit_car.html', car=data, form=form)


@index_bp.route("/cars/<car_id>/report", methods=["POST", "GET"])
@login_required
@restrict_user_type(["A"])
def report_car(car_id):
    res = CarsApi.get_car(car_id)
    if "OK" not in res.status:
        flash("car not found", 'warning')
        return redirect(url_for('main.home'))
    car = res.get_json()
    form = ReportCarForm()
    if form.validate_on_submit():
        r = ReportApi.new_car_report(
            car_id, json_data={'description': form.report.data})
        if r.status_code != 201:
            flash(r.get_json()['error'], "danger")
        else:
            flash("report submitted", "success")
            return redirect(url_for('main.home'))
    return render_template('report_car.html', car=car, form=form)


class BluetoothSearchForm(FlaskForm):
    search = SubmitField('Search For Devices')


class BluetoothResultForm(FlaskForm):
    bt_devices = SelectField('Bluetooth Devices')
    submit = SubmitField('Register Device')


@index_bp.route("/bluetooth/register", methods=["GET", "POST"])
@login_required
@restrict_user_type(["E"])
@load_query_params
def register_bluetooth(query_params={}):
    search_form = BluetoothSearchForm()
    results_form = BluetoothResultForm()
    form_keys = [*request.form.keys()]
    if 'search' in form_keys and search_form.validate_on_submit():
        res = BluetoothApi.search()
        if res.status_code == 200:
            bluetooth_devices = res.get_json()
            choices = []
            for device in bluetooth_devices:
                choices.append((device['bd_addr'],
                                "{} - {}".format(device['device_name'],
                                                 device['bd_addr'])))
            if choices:
                results_form.bt_devices.choices = choices
            else:
                flash("no devices found, try again", 'danger')
        else:
            print(res.get_json())
            flash('Search failed: {}'.format(res.get_json()['error']),
                  'danger')
    if 'submit' in form_keys:
        res = AuthApi.auth_update_user(
            json_data={'bd_addr': results_form.bt_devices.data})
        if res.status_code == 200:
            flash(
                "Successfully registered bluetooth device: {}".format(
                    results_form.bt_devices.data), 'success')
            if query_params.get('href'):
                return redirect(query_params['href'])
            else:
                return redirect(url_for('main.engineer'))
        else:
            print(res.get_json())
            flash('bluetooth device registration failed: {}'.format(
                res.get_json()['error']))

    return render_template("register_bluetooth.html",
                           search_form=search_form,
                           results_form=results_form)


class CarReportButtonOps:
    supported = {"submit_enablebluetooth", "submit_lockcar"}

    @staticmethod
    def submit_enablebluetooth(car_id, report_id):
        bd_addr = g.user.bd_addr
        if not bd_addr:
            href = url_for('main.view_car_report',
                           car_id=car_id,
                           report_id=report_id)
            link = "<a href='{}'><button class='btn btn-link'>{}</button></a>"\
                .format(url_for('main.register_bluetooth', href=href),
                        "To activate bluetooth register a bluetooth device " +
                        "<b>here</b>")
            flash(Markup(link), 'info')
        # engineer must register bluetooth MAC address BluetoothApi =>
        #       masterservice bluetooth scan
        else:
            res = CarsApi.Bluetooth.proximity_unlock(
                car_id, json_data={"bd_addr": bd_addr})
            if res.status_code == 200:
                flash("Succesfully enabled bluetooth proximity unlock",
                      "success")
                flash(
                    "Bluetooth search ends at {}".format(
                        datetime.fromtimestamp(
                            res.get_json()['expiration_time'])), "info")
            else:
                flash("Error: {}".format(res.get_json()['error']), 'danger')

    @staticmethod
    def submit_lockcar(car_id, _):
        res = CarsApi.patch_car(id=car_id, json_data={'locked': True})
        if res.status_code == 200:
            flash("car locked", 'success')
        else:
            flash("Error: {}".format(res.get_json()['error']), 'danger')


@index_bp.route('/cars/<car_id>/report/<report_id>', methods=["GET", "POST"])
@login_required
@restrict_user_type(["E"])
def view_car_report(car_id, report_id):
    if request.method == 'POST':
        submitted = [*request.form.keys()]
        for operation in submitted:
            if operation in CarReportButtonOps.supported:
                getattr(CarReportButtonOps, operation)(car_id, report_id)

    car = None
    report = None
    rep_res = ReportApi.get_car_report(car_id, report_id)
    car_res = CarsApi.get_car(car_id)
    if rep_res.status_code != 200:
        flash('could not find car report', 'danger')
    else:
        report = rep_res.get_json()
        car = car_res.get_json()
        car['reports'] = [report]

    if report['resolved']:
        flash("Report {} has been resolved".format(report_id), 'info')
        return redirect('main.engineer')

    return render_template('view_car_report.html', report=report, cars=[car])


@index_bp.route('/manager')
@login_required
@restrict_user_type(["M"])
def manager():
    '''
    Manager Home Page: Displays a managers home page

    :return: Rendered web page of the manager.html
    '''
    return render_template('manager.html')


# Can be removed, still testing on it.
@index_bp.route('/admin')
@login_required
@restrict_user_type(["A"])
def admin():
    '''
    Manager Home Page: Displays a managers home page

    :return: Rendered web page of the manager.html
    '''
    form = CarSearchForm()
    if form.is_submitted():
        url = url_for('main.all_cars', **request.form.to_dict(flat=False))
        return redirect(url)

    cars = []
    r = CarsApi.get_all_cars(query_params=request.args)

    if "OK" in r.status:
        cars = r.get_json()
        if len(cars) == 0:
            flash(
                "No options found matching your search, try broadening your\
                    criteria", "primary")
    else:
        flash("{}".format(r.get_json()['error']), 'danger')
    return render_template('admin.html', cars=cars, form=form)


@index_bp.route('/users', methods=['GET', 'POST'])
@login_required
@restrict_user_type(["A"])
def users():
    '''
    Lists the users that are in the system, this is sent to the user page.

    variable users: A json variable that holds the data from the users database
    in json form
    varaible r: Gets all users from the API, and sends them to ``users``
    if **OK** optional: a form can be submitted containing
    filtering options, the query parameters from the form will
    be added to the url then the page will be
    reloaded. The endpoint adds the URL's query parameters
    to the user API call's
    query parameters to filter the returned Users
    :type users: List of type database.model.user
    :type r: UsersApi

    :return: Returns users.html with the users data being sent
    :rtype: HTML/CSS

    '''

    form = UserSearchForm()
    if form.is_submitted():
        url = url_for('main.users', **request.form.to_dict(flat=False))
        return redirect(url)

    users = []
    r = UsersApi.get_all_users(query_params=request.args)

    if "OK" in r.status:
        users = r.get_json()
        if len(users) == 0:
            flash(
                "No options found matching your search, try broadening your\
                    criteria", "primary")
    else:
        flash("{}".format(r.get_json()['error']), 'danger')
    return render_template('users.html', users=users, form=form)


@index_bp.route("/users/<user_id>/edit", methods=["POST", "GET"])
@login_required
@restrict_user_type(["A"])
def edit_user(user_id):
    form = EditUserForm()
    if form.validate_on_submit():
        res = UsersApi.patch_user(user_id,
                                  json_data={
                                      'username': form.username.data,
                                      'firstname': form.firstname.data,
                                      'lastname': form.lastname.data,
                                      'userType': form.userType.data,
                                      'email': form.email.data,
                                      'pushbullet': form.pushbullet.data,
                                      'br_address': form.br_address.data
                                  })
        if res.status_code == 200:
            flash("user information updated successfully", "success")
        else:
            flash("Edit request error: {}".format(res.get_json()['error']),
                  'danger')
    else:
        res = UsersApi.get_user(user_id)
        if res.status_code != 200:
            flash("Data request error: {}".format(res.get_json()["error"]),
                  'warning')
            return redirect(url_for('main.users'))
    if form.is_submitted() and not form.validate():
        for (key, value) in form.errors.items():
            flash("Field {}: {}".format(key, value), 'danger')
    data = res.get_json()
    return render_template('edit_user.html', user=data, form=form)


@index_bp.route('/rental_history')
@login_required
@restrict_user_type(["A"])
def rental_history():
    """
    Rental History:
    This page will show you all about all the previous bookings
    of the entire system

    Booking Variable gets Jsonified bookings of all the previous bookings
    and active ones

    Returns a rendered history page.

    """
    bookings = []
    res = BookingApi.get_bookings()
    if "OK" in res.status:
        bookings = res.get_json()
    else:
        flash("{}".format(res.get_json()['error']), "danger")
    return render_template('rental_history.html', bookings=bookings)


@index_bp.route('/engineer')
@login_required
@restrict_user_type(["E"])
def engineer():
    '''
    Engineer Home Page: Displays a engineer home page

    :return: Rendered web page of the engineer.html
    '''
    cars = ReportApi.get_all_reports().get_json()
    return render_template('engineer.html', cars=cars)


@index_bp.route("/cars/new", methods=["POST", "GET"])
@login_required
@restrict_user_type(["A"])
def add_car():
    '''
    Add car page for displayed to the admin
    '''
    form = EditCarForm()
    if form.validate_on_submit():
        res = CarsApi.add_car(
            json_data={
                'make': form.make.data,
                'body_type': form.body_type.data,
                'colour': form.colour.data,
                'seats': form.seats.data,
                'costPerHour': form.cost.data,
                'lat': form.lat.data,
                'lng': form.lng.data
            })
        if res.status_code == 200:
            flash("Car created successfully", "success")
            return redirect(
                url_for('main.edit_car', car_id=res.get_json()['id']))

        else:
            flash("Edit request error: {}".format(res.get_json()['error']),
                  'danger')

    if form.is_submitted() and not form.validate():
        for (key, value) in form.errors.items():
            flash("Field {}: {}".format(key, value.pop()), 'danger')

    return render_template('add_car.html', form=form, car=None)
