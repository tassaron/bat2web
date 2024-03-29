# Run a development server

if [ -z "$1" ]; then
    port=5000
else
    port="$1"
fi

uwsgi --socket 0.0.0.0:$port --protocol=http -w bat2web:app --need-app --workers 6 --master --shared-import uwsgi_debug_log.py
