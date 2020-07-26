import configparser
import pdb
import wsgiref
from datetime import datetime
from urllib import parse
from wsgiref.simple_server import make_server

from stravalib.client import Client

import pandas as pd

config = configparser.ConfigParser()
config.read("config.ini")

client = Client()


class _RedirectWSGIApp(object):
    def __init__(self, success_message="Authorized!"):
        self.last_request_uri = None
        self._success_message = success_message

    def __call__(self, environ, start_response):
        start_response("200 OK", [("Content-type", "text/plain")])
        self.last_request_uri = wsgiref.util.request_uri(environ)
        return [self._success_message.encode("utf-8")]


def update_configfile(response):
    for k, v in response.items():
        config["strava"][k] = str(v)

    with open("config.ini", "w") as configfile:
        config.write(configfile)


def get_first_time_token():
    wsgi_app = _RedirectWSGIApp()

    with make_server("localhost", 5000, wsgi_app) as httpd:
        print("Serving on port 5000...")

        authorize_url = client.authorization_url(
            client_id=config["strava"]["client_id"],
            redirect_uri="http://localhost:5000/authorized",
            scope=config["strava"]["scopes"].split(","),
        )

        print(f"Go to {authorize_url}")

        httpd.handle_request()

    authorization_response = wsgi_app.last_request_uri

    qp = parse.parse_qs(parse.urlsplit(authorization_response).query)
    code = qp["code"][0]

    token_response = client.exchange_code_for_token(
        client_id=config["strava"]["client_id"],
        client_secret=config["strava"]["client_secret"],
        code=code,
    )
    update_configfile(token_response)


def authenticate():
    if "refresh_token" not in config["strava"]:
        get_first_time_token()

    elif "access_token" in config["strava"]:
        expires_at = config["strava"]["expires_at"]
        expires_at = datetime.fromtimestamp(int(expires_at))

        if expires_at < datetime.now():
            refresh_response = client.refresh_access_token(
                client_id=config["strava"]["client_id"],
                client_secret=config["strava"]["client_secret"],
                refresh_token=config["strava"]["refresh_token"],
            )
            update_configfile(refresh_response)

    client.access_token = config["strava"]["access_token"]
    client.refresh_token = config["strava"]["refresh_token"]
    client.expires_at = config["strava"]["expires_at"]


if __name__ == "__main__":
    authenticate()

    activities = list(client.get_activities(after="2020-07-01T00:00:00Z", limit=1000))
    acts = [{"id": a.id, **a.to_dict()} for a in activities]
    df = pd.DataFrame(acts)
    df2 = df[["type", "start_date", "name", "private", "distance", "id"]]
    df2 = df2[df2.type == "Ride"]
    df2.to_csv("private-rides.csv", index=False)
