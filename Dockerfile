FROM python

ENV TZ=Canada/Eastern

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /srv/funtimes

RUN pip install flask uwsgi

COPY /batchfile.py/batchfile ./batchfile

COPY /batchfile.py/setup.py .

RUN pip install .

COPY /batchfile.py/games/funtimes ./game

COPY bat2web.py .

COPY uwsgi.ini .

COPY /templates ./templates

COPY /img ./img

EXPOSE 5000

CMD ["uwsgi", "--ini", "uwsgi.ini"]

# Test server without Nginx
#CMD ["uwsgi", "--socket", "0.0.0.0:5000", "--protocol=http", "-w", "bat2web:app"]