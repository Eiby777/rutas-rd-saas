#!/bin/sh

set -e

# Esperar a que la base de datos esté lista
echo "Waiting for database..."
sleep 5

# Aplicar migraciones
echo "Applying database migrations..."
python manage.py migrate --noinput

# Crear superusuario si no existe
echo "Creating superuser if needed..."
python create_superuser.py

# Iniciar el servidor
echo "Starting server..."
exec "$@"
