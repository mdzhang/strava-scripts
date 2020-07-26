activities:
	curl -X GET "https://www.strava.com/api/v3/athlete/activities?after=1625097600&per_page=30" -H  "accept: application/json"

run:
	FLASK_APP=app.py flask run
