"""
Turns a .bat file into a website for some reason
"""
import batchfile
import flask
import os
import uuid
import logging
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def create_app():
    app = flask.Flask(__name__)

    # Create random secret key at first launch
    # Load from key.sav every subsequent launch
    try:
        with open("key.sav", "rb") as f:
            key = f.read(16)
    except FileNotFoundError:
        key = os.urandom(16)
        with open("key.sav", "wb") as f:
            f.write(key)

    app.secret_key = key
    app.config.update(
        #SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    return app


app = create_app()

LOG = logging.getLogger(__name__)
BAT_DIR = os.getenv("BAT_DIR", "/home/b/code/batchfile.py/games/funtimes")
BAT_FILE = "funtimes.bat"


class CookieRedirect:
    """
    TODO: redirect saving and loading files into a cookie
    """

    class CookieReader:
        def __init__(self, name):
            self.obj = name  # flask.request.get_cookie(name)

        def __enter__(self):
            return self.obj

        def __exit__(self, type, value, traceback):
            pass

    def __init__(self):
        self.files = {}

    def create(self, name, text):
        self.files[name] = [text]

    def append(self, name, text):
        self.files[name].append(text)

    def move(self, orig, dest):
        pass

    def remove(self, item):
        del self.files[item]

    def read(self, name):
        return CookieRedirect.CookieReader(self.files[name])

    def exists(self, name):
        return name in self.files


class Webpage:
    def __init__(self, uuid: uuid.UUID, user_input=""):
        self.uuid = uuid
        self.page_content = []
        self.page_content_as_html = ""
        self.user_input = user_input

    def append(self, line):
        self.page_content.append(line)

    def clear(self):
        self.__init__(self.uuid)

    def request_input(self):
        # triggers when input is needed from user
        # so we pause until this input is received from the webpage
        if self.page_content_as_html == "":
            self.page_content_as_html = "".join(self.page_content)
        #raise batchfile.PauseProgram
        #return None
        return self.user_input


def start_new_session():
    session_id = uuid.uuid4()
    webpage = Webpage(session_id)
    flask.session["uuid"] = session_id
    bat = batchfile.Batchfile(
        stdin=webpage.request_input, stdout=webpage, redirection=CookieRedirect()
    )
    try:
        bat.run([f"cd {BAT_DIR}", f"call {BAT_FILE}"])
    except batchfile.PauseProgram:
        flask.session["variables"] = bat.VARIABLES
        flask.session["callstack"] = bat.CALLSTACK
        return bat


def continue_session(next_input=""):
    webpage = Webpage(flask.session["uuid"], user_input=next_input)
        
    bat = batchfile.Batchfile(
        stdin=webpage.request_input, stdout=webpage, redirection=CookieRedirect()
    )
    try:
        bat.resume_from_serialized_state(flask.session["callstack"], flask.session["variables"])
    except batchfile.PauseProgram:
        flask.session["variables"] = bat.VARIABLES
        flask.session["callstack"] = bat.CALLSTACK
        return bat
    except (FileNotFoundError, IndexError):
        del flask.session["uuid"]


@app.route("/input", methods=["POST"])
def send_input():
    if "uuid" not in flask.session:
        return {"bat": None, "html": ""}
    
    user_input = flask.request.get_json()
    if user_input == "":
        user_input = " "
    elif user_input in ("A", "B", "C", "D", "Stats", "Stop"):
        # inelegant quick fix for case sensitivity, #FIXME
        user_input = user_input.lower()

    bat = continue_session(user_input)
    if bat is None:
        flask.abort(500)
    
    response = flask.make_response(
        {
            "html": bat.stdout.page_content_as_html,
            "bat": bat.CALLSTACK[-1][0],
        },
        200,
    )
    return response


@app.route("/")
def index():
    if "uuid" not in flask.session:
        # A brand new session
        bat = start_new_session()
    else:
        # Resume a session
        bat = continue_session()
        if bat is None:
            bat = start_new_session()

    if bat is None:
        flask.abort(400)

    flask_response = flask.make_response(
        flask.render_template(
            "webpage.html",
            content=bat.stdout.page_content_as_html,
            current_bat=bat.CALLSTACK[-1][0],
        ),
        200,
    )
    return flask_response


@app.route("/quit")
def user_requested_quit():
    if "uuid" in flask.session:
        uuid = flask.session.pop("uuid")
    return flask.redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
