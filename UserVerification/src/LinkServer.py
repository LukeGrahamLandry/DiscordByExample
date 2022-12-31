from flask import Flask
from UserVerification.src import DataAccess
app = Flask(__name__)


@app.route("/")
def home():
    return "https://github.com/LukeGrahamLandry/PycordByExample/UserVerification"


@app.route("/verify/<session>")
def verify_user(session):
    was_valid_session = DataAccess.set_verified(session)
    if was_valid_session:
        return "Your discord account has been linked. You may now speak in the server."
    else:
        return "Invalid Session. Please request a new link from the bot."


def start():
    app.run(host="0.0.0.0", port=3000)
