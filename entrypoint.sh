#!/bin/sh
set -e

cd pdfding

if [ "$DATABASE_TYPE" = "POSTGRES" ]; then
  POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
  POSTGRES_PORT="${POSTGRES_PORT:-5432}"
  echo "Waiting for postgres..."

  while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
    sleep 0.1
  done

  echo "PostgreSQL started"
fi

python manage.py migrate
python manage.py clean_up

if [ "$BACKUP_ENABLE" = "TRUE" ] || [ "$BACKUP_ENABLE" = True ] || [ "$CONSUME_ENABLE" = "TRUE" ] || [ "$CONSUME_ENABLE" = True ]; then
  python manage.py run_huey &
fi

HOST_PORT="${HOST_PORT:-8000}"
WORKERS="${WORKERS:-1}"
THREADS="${THREADS:-3}"
WORKER_TIMEOUT="${WORKER_TIMEOUT:-30}"

exec python -m gunicorn --bind 0.0.0.0:$HOST_PORT --workers $WORKERS --threads $THREADS --timeout $WORKER_TIMEOUT core.wsgi:application
