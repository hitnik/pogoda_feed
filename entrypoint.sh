#!/bin/sh

python manage.py migrate
python manage.py collectstatic --no-input --clear
python manage.py loaddata hazard_feed/fixtures/hazard_levels.json

exec "$@"
