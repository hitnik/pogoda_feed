#!/bin/sh

python manage.py migrate
python manage.py loaddata hazard_feed/fixtures/hazard_levels.json
python manage.py collectstatic --no-input --clear


exec "$@"
