#!/bin/sh

python manage.py rqworker high default low

exec "$@"
