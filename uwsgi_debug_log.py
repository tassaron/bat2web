import uwsgi, logging

uwsgi_log = logging.getLogger(uwsgi.__package__)
uwsgi_log.setLevel(logging.DEBUG)
