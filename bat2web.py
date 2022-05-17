"""
Turns a .bat file into a website for some reason
"""
import batchfile
import flask
import os
import threading
import queue
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
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    return app


app = create_app()

LOG = logging.getLogger(__name__)
BAT_DIR = os.getenv("BAT_DIR", "/srv/funtimes/game")
BAT_FILE = "funtimes.bat"

# Queues and threads for batchfile interpreters
input_queue = queue.Queue()
session_threads = {}


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
    def __init__(self, uuid: uuid.UUID):
        self.uuid = uuid
        self.page_content = []
        self.page_content_as_html = ""

    def append(self, line):
        self.page_content.append(line)

    def clear(self):
        self.__init__(self.uuid)

    def request_input(self):
        if self.page_content_as_html == "":
            self.page_content_as_html = "".join(self.page_content)
        try:
            uuid, line = input_queue.get(timeout=600)
            while uuid != self.uuid:
                input_queue.put((uuid, line))
                uuid, line = input_queue.get(timeout=600)
        except queue.Empty:
            # kill batchfile after 10 minutes of inactivity
            raise batchfile.QuitProgram
        if line.lower() == "quit":
            raise batchfile.QuitProgram
        return line


def start_session_thread(bat: batchfile.Batchfile):
    bat.run([f"cd {BAT_DIR}", f"call {BAT_FILE}"])


@app.route("/input", methods=["POST"])
def send_input():
    if "uuid" not in flask.session:
        return {"bat": None, "html": ""}
    user_input = flask.request.get_json()
    session_threads[flask.session["uuid"]].stdout.clear()
    if user_input == "":
        user_input = " "
    elif user_input in ("A", "B", "C", "D", "Stats", "Stop"):
        # inelegant quick fix for case sensitivity, #FIXME
        user_input = user_input.lower()
    input_queue.put((flask.session["uuid"], user_input))
    while session_threads[flask.session["uuid"]].stdout.page_content_as_html == "":
        continue
    response = flask.make_response(
        {
            "html": session_threads[flask.session["uuid"]].stdout.page_content_as_html,
            "bat": session_threads[flask.session["uuid"]].current_bat,
        },
        200,
    )
    return response


@app.route("/")
def index():
    if "uuid" not in flask.session:
        # A brand new session
        session_id = uuid.uuid4()
        webpage = Webpage(session_id)
        bat = batchfile.Batchfile(
            stdin=webpage.request_input, stdout=webpage, redirection=CookieRedirect()
        )
        global session_threads
        session_threads[session_id] = bat
        flask.session["uuid"] = session_id
        session_thread = threading.Thread(
            group=None,
            target=start_session_thread,
            name="Batchfile Execution Thread",
            args=(bat,),
        )
        session_thread.start()
        LOG.warning("Threads now in existence: %s", str(threading.active_count()))

    while session_threads[flask.session["uuid"]].stdout.page_content_as_html == "":
        continue
    flask_response = flask.make_response(
        flask.render_template(
            "webpage.html",
            content=session_threads[flask.session["uuid"]].stdout.page_content_as_html,
            current_bat=session_threads[flask.session["uuid"]].current_bat,
        ),
        200,
    )
    return flask_response


@app.route("/quit")
def user_requested_quit():
    if "uuid" in flask.session:
        uuid = flask.session.pop("uuid")
        input_queue.put((uuid, "quit"))
    return flask.redirect("/")


if __name__ == "__main__":
    app.run()
