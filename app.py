from flask import Flask, render_template, session, redirect, request, url_for, g, logging, flash
from twitterUtils import get_request_token, get_oauth_verifier_url, get_access_token
from cleanUser import User, User2
from database import Database, CursorFromConnectionFromPool
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, BooleanField
from passlib.hash import sha256_crypt
import psycopg2

"""" Here you can initialize your database """ 

app = Flask(__name__)
# the secret key is necessary so that the app can cookies can remain secure
app.secret_key = '3456'


# we want to access the user object in every method
@app.before_request
def load_user():
    if 'screen_name' in session:
        # the g variable does not die off when we execute this method, it is globally available,
        # available throughout the entire request
        g.user = User.load_from_db_by_screen_name(session['screen_name'])


@app.route('/')
def homepage():
    return render_template('home.html')

# we are now creating a new route which will allow users to login with twitter
# the process of getting access to twitter is getting the request token, get oauth verifier and get access token


@app.route('/login/twitter')
def twitter_login():
    # redirecting the user to their profile if they are already logged in, if their screen_name is still in session
    if 'screen_name' in session:
        return redirect(url_for('profile'))
    request_token = get_request_token()
    session['request_token'] = request_token

    return redirect(get_oauth_verifier_url(request_token))


@app.route('/logout')
def logout():
    session.clear()
    # redirects the user to a page, url_for calculates the url that we are redirecting to by getting
    # the associated endpoint to the method homepage
    return redirect(url_for('homepage'))


@app.route('/contacts')
def contacts():
    return render_template('contacts.html')


@app.route('/oauth/twitter')
def twitter_oauth():
    # its gonna extract the value of oauth_verifier and put it in the variable
    # args are the query string parameters(oauth_verifier122343)
    oauth_verifier = request.args.get('oauth_verifier')
    # the request token is in the session therefore we just retrieve it from the session
    access_token = get_access_token(session['request_token'], oauth_verifier)

    # we now wanna create the users and store them in the database so that they don't have to login always
    # we are gonna load the user by screen name
    user = User.load_from_db_by_screen_name(access_token['screen_name'])
    # if the screen_name doesn't exist we are gonna create the user
    if not user:
        user = User(access_token['screen_name'], access_token['oauth_token'], access_token['oauth_token_secret'], None)
        user.save_to_db()

    # we now want to save the screen_name to the session just so we remember who the user is so when they come back
    session['screen_name'] = user.screen_name

    # we redirect by returning the profile method
    return redirect(url_for('profile'))


@app.route('/profile')
def profile():
    # we are passing the variable for the template screen_name, the variable is gonna be equal to the session screen
    # name
    return render_template('profile.html')


@app.route('/search')
def search():
    query = request.args.get('q')
    tweets = g.user.twitter_request('https://api.twitter.com/1.1/search/tweets.json?q={}'.format(query))

    # get the tweet's text for each of the tweets in tweet statuses
    tweet_texts = [tweet['text'] for tweet in tweets['statuses']]

    return render_template('search.html', content=tweet_texts)


# creating the about page
@app.route('/about')
def about_page():
    return render_template('about.html')


# the signUp page
class SignUp(Form):
    name = StringField('Name', [validators.Length(min=1, max=30)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=30)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


@app.route('/signup', methods=['GET', 'POST'])
def register():
    form = SignUp(request.form)
    if request.method == 'POST' and form.validate():
        user2 = User2(form.email.data, form.name.data, form.username.data, sha256_crypt.encrypt(str(form.password.data)))
        user2.register()
        flash('You are now registered, you may login', 'success')

        # user2 = User2.load_from_db_by_username("username")
        # session['screen_name'] = user2.screen_name

        # return redirect(url_for('profile'))
    return render_template('signUp.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'screen_name' in session:
        return redirect(url_for('profile'))
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        """ create a connection with psychopg2 here 
        I have left out this part since it contains passwords
        """
        result = cursor.fetchall()
        if result:
            for row in result:
                password = row[4]
                if sha256_crypt.verify(password_candidate, password):
                    session['logged_in'] = True
                    session['screen_name'] = username
                    flash('login successful', 'success')
                    return redirect(url_for('profile'))
                else:
                    flash('Incorrect password, try again', 'danger')
        else:
            flash('The user does not exist, try signing up', 'danger')
            # return redirect(url_for('homepage'))
    return render_template('login.html')


if __name__ == "__main__":
    app.run(port=5001, debug=True)
