import os

from authlib.integrations.flask_client import OAuth
from flask import Flask, jsonify, session, url_for

app = Flask(__name__)
app.config.update(SECRET_KEY="colossal-enjoyment")

oauth = OAuth(app)

strava = oauth.register(
    "strava",
    api_base_url="https://www.strava.com/api/v3",
    access_token_url="https://www.strava.com/api/v3/oauth/token",
    authorize_url="https://www.strava.com/api/v3/oauth/authorize",
    client_id=os.environ["STRAVA_CLIENT_ID"],
    client_secret=os.environ["STRAVA_CLIENT_SECRET"],
)


@app.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    return strava.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    token = strava.authorize_access_token()
    session["strava_token"] = token
    profile = strava.get("/user", token=token)
    return jsonify(profile)
