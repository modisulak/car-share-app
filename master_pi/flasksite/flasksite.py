from flask import Flask, render_template, url_for, flash, redirect

from master_pi.flasksite.forms import (RegisterForm, LoginForm, CarSearchForm)

app = Flask(__name__)
'''
Secret Key:
preventing issues with other people trying to use a form
'''
app.config['SECRET_KEY'] = '8096fca8544fc48d3cf7767a43f61fe5'

cars = [
    {
        'id': '1',
        'make': 'Honda Civic',
        'body_type': 'Sedan',
        'colour': 'Blue',
        'seats': '5',
        'location': 'Melbourne',
        'available': 'Available'
    },
    {
        'id': '2',
        'make': 'Honda Civic',
        'body_type': 'Sedan',
        'colour': 'Blue',
        'seats': '5',
        'location': 'Melbourne',
        'available': 'Available'
    },
    {
        'id': '3',
        'make': 'Honda Civic',
        'body_type': 'Sedan',
        'colour': 'Blue',
        'seats': '5',
        'location': 'Melbourne',
        'available': 'Available'
    },
    {
        'id': '4',
        'make': 'Honda Civic',
        'body_type': 'Sedan',
        'colour': 'Blue',
        'seats': '5',
        'location': 'Melbourne',
        'available': 'Unavailable'
    },
    {
        'id': '5',
        'make': 'Honda Civic',
        'body_type': 'Sedan',
        'colour': 'Blue',
        'seats': '5',
        'location': 'Melbourne',
        'available': 'Unavailable'
    },
]


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])  # Alias for the default
def home():
    form = CarSearchForm()
    '''
    Home Page:
    The main page that lists the cars
    '''
    return render_template('home.html', cars=cars, form=form)


@app.route('/about')  # Sets URL Line
def about():
    """
    About Page:
    This page will show you all about the app
    """
    return render_template('about.html')


@app.route('/history')  # Sets URL Line
def history():
    """
    History Page:
    This page will show the user the previous history of cars they have hired
    """
    return render_template('history.html', cars=cars)


@app.route('/booking', methods=['GET', 'POST'])  # Sets URL Line
def booking():
    """
    Booking Page:
    This page will show a form that allows you to book or hire a car
    """
    return render_template('booking.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    '''
    Register:
    Registers user using form
    '''
    form = RegisterForm()
    if form.validate_on_submit():
        flash("Account created for {}!".format(form.username.data), 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Login
    Logs user in if they have correct credentials
    '''
    form = LoginForm()
    if form.validate_on_submit():
        # This is just a test for the admin data to simulate successful login
        if form.username.data == 'admin' and form.password.data == 'pass':
            flash("Logged in user {}!".format(form.username.data), 'success')
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password',
                  'danger')
    return render_template('login.html', title='Login', form=form)


if __name__ == "__main__":
    app.run(debug=True)
