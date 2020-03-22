#!/bin/sh

git clone https://github.com/hitnik/pogoda_feed.git ./


python manage.py migrate
python manage.py collectstatic --no-input

exec "$@"
