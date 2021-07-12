"""
The setup for this app is to have everything related to login here,
and then we'll integrate the other routes by using blueprints.
    app.register_blueprint(..., url_prefix="/rest") -> routes for user calls in python
    app.register_blueprint(..., url_prefix="/rest_admin") -> admin stuff for us (backdoor)
    app.register_blueprint(..., url_prefix="/user") -> html stuff for users

"""

# Python standard libraries
import json
import os

# Third party libraries
from flask import Flask, redirect, request, url_for, render_template
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

from user import User
import routes_rest
# import routes_rest_admin


# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)


# When testing, we don't want to enforce authentication.
# This overrides the @login_required decorator, but not
# manual checks that we do.
# The `FLASK_LOGIN_DISABLED` flag is something we invented.
# It is not part of the usual flags for Flask.
# The `current_user` will be a flask_login.mixins.AnonymousUserMixin
# as described on 
# https://flask-login.readthedocs.io/en/latest/_modules/flask_login/mixins.html
if (os.environ.get('FLASK_LOGIN_DISABLED', "False")
   in ["True", "true", "1"]):
    app.config['LOGIN_DISABLED'] = True


# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)



@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403

# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    # TODO : Implement this. Check if user is part of @mila.quebec,
    # among other things, but also check if we didn't intend on
    # locking that user out or something.
    return User.get(user_id)


@app.route("/")
def index():
    if current_user.is_authenticated:
        return render_template("index_inside.html",
            user={  'name': current_user.name,
                    'email': current_user.email,
                    'profile_pic': current_user.profile_pic,
                    'status': current_user.status,
                    'biblioplex_api_key': current_user.biblioplex_api_key}
            )
        #return (
        #    "<p>Hello, {}! You're logged in! Email: {}</p>"
        #    "<div><p>Google Profile Picture:</p>"
        #    '<img src="{}" alt="Google profile pic"></img></div>'
        #    '<a class="button" href="/logout">Logout</a>'.format(
        #        current_user.name, current_user.email, current_user.profile_pic
        #    )
        #)
    else:
        return render_template("index_outside.html")
        # return '<a class="button" href="/login">Google Login</a>'


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # There are already mechanisms in place to that login
    # is restricted to users within the organization only.
    # It yields 
    #     Error 403: org_internal
    #     This client is restricted to users within its organization.
    # However, we might as well keep this check here also,
    # in case we ever reconfigure the authentication and get it wrong.
    if not users_email.endswith('@mila.quebec'):
        return "Will only create accounts for people with @mila.quebec accounts.", 400

    # Create a user in our db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add to database
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)
    login_user(user)
    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()




# in development

@login_required
@app.route("/index_inside")
def route_index_inside():
    return render_template("index_inside.html",
        user={  'name': "",
                'email': "",
                'profile_pic': "",
                'status': "enabled",
                'biblioplex_api_key': ""}
            )

def get_fake_current_user():
    current_user = lambda x: 1
    current_user.is_authenticated = True
    current_user.name = "Debug Guillaume Alain"
    current_user.email = "debug_guillaume.alain@mila.quebec"
    current_user.status = "enabled"
    current_user.email = "debug_guillaume.alain@mila.quebec"
    current_user.profile_pic = "https://lh6.googleusercontent.com/-ZpGnIkzbpjs/AAAAAAAAAAI/AAAAAAAAAAA/AMZuucnk_MYZRbu6xhHdHgXcp32j8VOTwg/s96-c/photo.jpg"
    current_user.biblioplex_api_key = "00000000000000000000000000000000"
    return current_user 

@app.route("/menu1")
def route_menu1():

    current_user = get_fake_current_user()

    if current_user.is_authenticated:
        return render_template("caterpie/inside_menu1.html",
            user={  'name': current_user.name,
                    'email': current_user.email,
                    'profile_pic': current_user.profile_pic,
                    'status': current_user.status,
                    'biblioplex_api_key': current_user.biblioplex_api_key}
            )
    else:
        return render_template("index_outside.html")

@app.route("/menu2")
def route_menu2():
    current_user = get_fake_current_user()

    if current_user.is_authenticated:
        return render_template("caterpie/inside_menu2.html",
            user={  'name': current_user.name,
                    'email': current_user.email,
                    'profile_pic': current_user.profile_pic,
                    'status': current_user.status,
                    'biblioplex_api_key': current_user.biblioplex_api_key}
            )
    else:
        return render_template("index_outside.html")

@app.route("/menu3")
def route_menu3():
    current_user = get_fake_current_user()

    if current_user.is_authenticated:
        return render_template("caterpie/inside_menu3.html",
            user={  'name': current_user.name,
                    'email': current_user.email,
                    'profile_pic': current_user.profile_pic,
                    'status': current_user.status,
                    'biblioplex_api_key': current_user.biblioplex_api_key}
            )
    else:
        return render_template("index_outside.html")




app.register_blueprint(routes_rest.flask_api, url_prefix="/rest")
# app.register_blueprint(routes_rest_admin.flask_api, url_prefix="/rest_admin")


if __name__ == "__main__":
    # app.run(ssl_context="adhoc")
    # When we're running locally, we're not going to do authentications,
    # we're only going to test the REST API, so let's not run with https.
    app.run()