#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py loaddata main/products_fixture.json || true
python manage.py createsuperuser --no-input || true   # uses DJANGO_SUPERUSER_* env vars
