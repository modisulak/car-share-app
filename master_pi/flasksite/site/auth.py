# credit to https://flask-wtf.readthedocs.io/en/latest/form.html#module-
# flask_wtf.file
# credit to https://stackoverflow.com/questions/21248718/
# how-to-flashing-a-message-with-link-using-flask-flash
from flask import (Blueprint, flash, session, redirect, render_template,
                   request, url_for, g, Markup, current_app as app)
import functools
from master_pi.flasksite import api
from master_pi.flasksite.db.models import User, Booking, AuthToken, RequestLog
from master_pi.flasksite.forms import (RegisterForm, LoginForm,
                                       FaceVideoUploadForm)
from flask_wtf import FlaskForm
from wtforms import SubmitField
from facial_recognition import FaceFile, FaceEncoding
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=('GET', 'POST'))
def register():
    '''
    Register forwards a register form for new users to register
    to be able to access the site

    :param g: Chesks if user is logged in, also requests api data
             in the form of json
    :param form: The form for the user to register their details
                to be sent to the database
    :param r: Api Register

    :type form: RegisterForm
    :type g: Object
    :type r: api


    :return: Returns register.html with the form being sent, along
            with the title of "register"
    :rtype: HTML/CSS

    '''
    if g.user is not None:
        return redirect(url_for("main.home"))
    form = RegisterForm()
    if form.validate_on_submit():
        g.api_request_json = {
            'username': form.username.data,
            'password': form.password.data,
            'email': form.email.data,
            'lastname': form.lastname.data,
            'firstname': form.firstname.data
        }
        r = api.AuthApi.auth_register()
        if "CREATED" in r.status:
            flash("Account created successfully", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("{}".format(r.get_json()['error']), 'danger')

    return render_template('register.html', title="Register", form=form)


@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    '''
    Login forwards a login form for new users to login
    to be able to access the site

    :param g: Chesks if user is logged in, also requests api data
             in the form of json
    :param form: The form for the user to login with their details
                to be sent to the database
    :param r: Api Register

    :type form: LoginForm
    :type g: Object
    :type r: api


    :return: Returns login.html with the form being sent, along
            with the title of "Login"
    :rtype: HTML/CSS

    '''
    if g.user is not None and g.user.userType != "M":
        return redirect(url_for("main.home"))
    form = LoginForm()
    if form.validate_on_submit():
        g.api_request_json = {
            'username': form.username.data,
            'password': form.password.data
        }
        r = api.AuthApi.auth_login()
        if "OK" in r.status:
            session.clear()
            data = r.get_json()
            session['user_id'] = str(data['user_id'])
            session['auth_token'] = data['token']
            if (data['userType'] in ["U", "A"]):
                return redirect(url_for("main.home"))
            elif data['userType'] == "M":
                return redirect(url_for("main.manager"))
            elif data['userType'] == "E":
                return redirect(url_for("main.engineer", ))
            else:
                flash("userType {} unknown".format(data['userType']))
                return redirect(url_for("main.home"))
        else:
            flash("{}".format(r.get_json()['error']), 'danger')

    return render_template('login.html', title="Login", form=form)


@auth_bp.route("/logout", methods=('GET', 'POST'))
def logout():
    '''
    Logout allows the users to sign out of the session

    :session: Ends the session and logs the user out

    :return: redirects the user back to the home page.
    :rtype: Redirect
    '''
    session.clear()
    g.user = None
    return redirect(url_for("auth.login"))


@auth_bp.before_app_request
def load_logged_in_user():
    '''
    Checks of the user is already logged in before any pages are displayed.

    :param user_id: Gets the user id from the current session
    :type user_id: session
    :param g: Sets the user to the user_id if they are logged in
    :type g: Object
    :param auth_token: Gets the auth_token from the current session
    :type auth_token: session
    '''
    user_id = session.get('user_id')
    user = None
    if user_id is None:
        g.user = None
    else:
        user = User.query.get(user_id)
        g.user = user

    auth_token = session.get('auth_token')
    g.auth_token = None if auth_token is None else auth_token

    # show facial recognition warning flash link for unencoded users
    current_booking = None
    if user and user.userType == "U" and len(user.userFace) < 1 and len(
            session.get('_flashes', [])) < 1:
        face_upload = url_for("auth.face_upload")
        face_encode = url_for("auth.face_encode")
        greenlist = [face_encode, face_upload, "/static/", "/api/"]
        if all(url not in request.url for url in greenlist):
            link = "<a href='{}'>{}</a>".format(
                face_upload,
                "Booking a car requires enabling facial recognition. Click Here"
            )
            flash(Markup(link), "danger")
            g.user_face_warning = 1

    if user:
        current_booking = Booking.query.filter_by(user_id=user.id,
                                                  active=True).first()
    g.current_booking = current_booking if current_booking else None

    # log request
    log_request()


def log_request():
    '''
    Logs each request made to the website
    '''
    user_id = None
    if g.user:
        user_id = g.user.id
    url = request.url[:2048] + (request.url[2048:] and '..')
    RequestLog.create_request_log({
        'request_url': url,
        'user_id': user_id,
        'date_created': str(datetime.now())
    })


def login_required(view):
    '''
    Checks if the user is logged in

    :return: redirect if the user is not logged in
    :rtype: Function
    '''
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        # redirect if user is None or user's AuthToken is None
        if g.user is None or AuthToken.query.filter_by(
                token=g.auth_token).first() is None:
            return redirect(url_for('auth.logout'))

        return view(*args, **kwargs)

    return wrapped_view


def restrict_user_type(user_type):
    '''
    :param user_type: list of strings matching user_type allowed to make request
    Wraps a http request view, checks whether user making request is in
    ``user_type``.
    :return: decorator that takes a view, returns wrapped_view function
    containing result of wrapped view or http error 401 Unauthorized
    :rtype: wrapped_view Function
    '''
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):
            res = None
            # redirect if user is not in user_type
            if g.user.userType not in user_type:
                flash("User not authorized to access resource", 'danger')
                res = redirect(url_for('main.home'))
            else:
                res = view(*args, **kwargs)
            return res

        return wrapped_view

    return decorator


@auth_bp.route("/face_upload", methods=('GET', 'POST'))
@login_required
def face_upload():
    # redirect if user face already exists
    if len(g.user.userFace) > 0:
        flash('user face encoding already exists', 'primary')
        return redirect(url_for('main.home'))

    form = FaceVideoUploadForm()

    # TODO validate video is small enough
    # TODO validate video is 7 seconds

    if form.validate_on_submit():
        f = form.file.data
        if not f:
            flash("file not found", "danger")
        else:
            file_path = FaceFile(app.instance_path).get_video_file_path(
                f.filename)
            f.save(file_path)
            session[FaceFile.session_video_name] = file_path
            # redirect to face encoding page
            return redirect(url_for('auth.face_encode'))

    return render_template('face_upload.html', form=form)


class EncodeFaceForm(FlaskForm):
    submit = SubmitField("Encode Face")


@auth_bp.route("/face_encode", methods=('GET', 'POST'))
@login_required
def face_encode():
    # redirect if user face already exists
    if len(g.user.userFace) > 0:
        flash('user face encoding already exists', 'primary')
        return redirect(url_for('main.home'))

    # redirect if no face file path in session
    file_path = session.get(FaceFile.session_video_name)
    if file_path is None:
        flash('Please upload face video before encoding', 'danger')
        return redirect(url_for('auth.face_upload'))

    form = EncodeFaceForm()

    if form.validate_on_submit():
        # encode face
        facefile = FaceFile(app.instance_path)
        dataset_path = facefile.get_dataset_path(g.user.username)
        classifier_file_path = facefile.get_classifier_file_path()
        try:
            # activate capture script
            # activate encode script
            fe = FaceEncoding(file_path, dataset_path, classifier_file_path)
            user_face_json_str = fe.create()
        except Exception as e:
            # if capture / encode fails, redirect back to face_upload form
            flash(
                'Unexpected error occured {}, please try again'.format(str(e)),
                'danger')
            return redirect(url_for('auth.face_upload'))

        g.api_request_json = {'userFace': user_face_json_str}
        res = api.AuthApi.auth_update_user(g.user.id)
        if "OK" in res.status:
            flash("Successfully encoded face, you're ready to book a car!",
                  "success")
            return redirect(url_for('main.home'))
        else:
            flash(
                'Unexpected error occured {}'.format(res.get_json()["error"]),
                'danger')
        # TODO delete video

    return render_template("face_encode.html", form=form)
