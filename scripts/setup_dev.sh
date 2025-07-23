#!/bin/bash
echo "🚀 Configurando entorno de desarrollo RutasRD SaaS..."

# Crear virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r backend/requirements/development.txt

# Configurar variables de entorno
cp backend/.env.example backend/.env
echo "📝 Edita backend/.env con tus configuraciones locales"

# Configurar base de datos
echo "🗄️ Configurando PostgreSQL..."
createdb rutas_rd || echo "La base de datos ya existe o no se pudo crear"
psql -U postgres -c "CREATE USER rutas_rd_user WITH PASSWORD 'dev_password_123';" || echo "El usuario ya existe o no se pudo crear"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE rutas_rd TO rutas_rd_user;" || echo "No se pudieron otorgar permisos"

# Ejecutar migraciones
cd backend
python manage.py migrate

# Crear superusuario
echo "👤 Creando superusuario..."
python manage.py createsuperuser --username admin --email admin@rutasrd.com --noinput || echo "El superusuario ya existe o no se pudo crear"

# Crear datos de muestra
python manage.py create_sample_data

echo "✅ Setup completo! Ejecuta 'python manage.py runserver' para iniciar"
