"""
Turns a .bat file into a website for some reason
"""
import batchfile
import flask
import os
import threading
import queue
import uuid

app = flask.Flask(__name__)
app.secret_key = os.urandom(16)
input_queue = queue.Queue()
session_threads = {}


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
        uuid, line = input_queue.get()
        while uuid != self.uuid:
            input_queue.put((uuid, line))
            uuid, line = input_queue.get()
        return line


def start_session_thread(bat: batchfile.Batchfile):
    bat.run("/home/b/bat2web/funtimes", "funtimes.bat")


@app.route("/", methods=["GET", "POST"])
def index():
    if flask.request.method == "GET" and "uuid" not in flask.session:
        # A brand new session
        session_id = uuid.uuid4()
        webpage = Webpage(session_id)
        bat = batchfile.Batchfile(stdin=webpage.request_input, stdout=webpage)
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
    elif flask.request.method == "POST":
        user_input = flask.request.form["user_input"]
        if user_input == "":
            user_input = " "
        session_threads[flask.session["uuid"]].stdout.clear()
        input_queue.put((flask.session["uuid"], user_input))

    while session_threads[flask.session["uuid"]].stdout.page_content_as_html == "":
        continue
    return flask.render_template(
        "webpage.html",
        content=session_threads[flask.session["uuid"]].stdout.page_content_as_html,
    )


if __name__ == "__main__":
    app.run()
