#!/bin/sh

git init .
git remote add origin https://github.com/hitnik/pogoda_feed.git
git pull origin master


python manage.py migrate
python manage.py loaddata email_templates.json
python manage.py collectstatic --no-input

exec "$@"
