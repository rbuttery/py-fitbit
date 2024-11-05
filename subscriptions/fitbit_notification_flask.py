from flask import Flask, request
import os
app = Flask(__name__)

# The endpoint for Fitbit notifications
@app.route("/fitbit-notifications", methods=["GET", "POST"])
def fitbit_notifications():
    verify_code = os.getenv('FITBIT_VERIFY_CODE')
    if request.method == "GET":
        # Fitbit will verify the endpoint with a GET request containing a "verify" query parameter
        verify_param = request.args.get("verify")
        if verify_param == verify_code:
            return "", 204  # Correct verification code
        else:
            return "", 404  # Incorrect verification code

    # Handle POST notifications
    if request.method == "POST":
        data = request.get_json()
        # Ensure we respond within 5 seconds to avoid being disabled by Fitbit
        print("Received notification:", data)
        # Respond with HTTP 204 No Content immediately
        return "", 204

# Run the Flask server
if __name__ == "__main__":
    app.run(port=5000)

# This server needs to be running publicly so that Fitbit can send notifications to it.
# NGROK or VS Code Port Forwarding can be used to make it publicly accessible for testing.
