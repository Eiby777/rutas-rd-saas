#!/bin/bash
echo "🧪 Ejecutando pruebas..."

cd backend

# Activar entorno virtual si existe
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

# Tests unitarios
echo "🚀 Ejecutando tests..."
python manage.py test --verbosity=2

# Coverage (opcional)
if command -v coverage &> /dev/null; then
    echo "📊 Generando reporte de cobertura..."
    coverage run --source='.' manage.py test
    coverage report
    coverage html
    echo "✅ Reporte HTML generado en htmlcov/"
fi

echo "✅ Pruebas completadas"
