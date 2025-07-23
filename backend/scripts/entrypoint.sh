#!/bin/sh

set -e

# Esperar a que la base de datos esté lista
echo "Waiting for database..."
sleep 5

# Aplicar migraciones
echo "Applying database migrations..."
python manage.py migrate --noinput

# Iniciar el servidor
echo "Starting server..."
exec "$@"
