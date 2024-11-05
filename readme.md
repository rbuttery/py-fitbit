# py-fitbit

Python wrapper for the Fitbit API.

I created this based on a fork of the original [python-fitbit](https://github.com/orcasgit/python-fitbit) library which occupies `pip install fitbit`. However the library was not maintained, and futhermore is not something I want to maintain or support. So I made a new one, but did use some of the original code, expecially in the `auth` module.

Improvements:
- Updated to use the latest Fitbit WebAPI endpoints.
- More "pythonic" code. Easier to read & write.
- Automated OAuth2 flow - no more manual browser interaction (except for initial scope selection) - this is complex so expect bugs at first.
- Includes a Flask server for handling Fitbit webhook notifications. This is the "subscriptions" endpoint, that can send webhooks to any URL. 
    - This needs to be setup with Fitbit separately as well.
    - ** TODO: Provide a guide on how to do this

## TODO:
- Client today is read-only. Need to add Create, Update, Delete (CRUD) endpoints for everything
- Error handling
- Logging
- Tests
- Documentation
- Example notebooks
- FITBIT_VERIFY_CODE in .env file is not automated yet - need to do this manually

## Also includes a Flask server for handling Fitbit webhook notifications.

### Windows Installation
```powershell
git clone https://github.com/rbuttery/py-fitbit.git
cd py-fitbit
python -m venv env
env\scripts\activate
pip install -r requirements.txt
```

### Setup the .env file
1. Go to https://dev.fitbit.com/apps/create and create a new app.
2. Use http://localhost:8080/ as the "Redirect URI"
3. Copy the Client ID and Client Secret into the .env file.

### Optionally (For Subscription Webhooks)
1. Setup the `FITBIT_VERIFY_CODE` to be used in the Flask server & subscriptions module, but this is not required.
2. Run the Flask server by running `python subscriptions/fitbit_notification_flask.py`
3. (optional) TODO: Create a guide for this -> Use Ngrok or Port Forwarding to get a public URL for the Flask server.
4. (optional) Go back to the Fitbit dev console and setup a new webhook using the FLASK_URL/fitbit-notifications as the "Subscription URL"

### A Basic Usage Example
```python
from fitbit.client import FitbitClient
fitbit = FitbitClient()
fitbit.get_profile()['user']['fullName']
```
