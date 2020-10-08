"""
Turns a .bat file into a website for some reason
"""
import batchfile
import flask


app = flask.Flask(__name__)


class Page:
    def __init__(self):
        self.page = []

    def append(self, line):
        self.page.append(line)

    def complete(self):
        self.webpage = "<br>".join(self.page)

    def send_input(self):
        self.complete()
        raise batchfile.QuitProgram

page = Page()
bat = batchfile.Batchfile(stdin=page.send_input, stdout=page)
bat.run("funtimes", "funtimes.bat")

@app.route("/")
def index():
    return page.webpage

if __name__ == '__main__':
    app.run()
