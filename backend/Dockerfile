# backend/Dockerfile
FROM python:3.11-slim

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements/ ./requirements/
RUN pip install --no-cache-dir -r requirements/development.txt

# Copiar código fuente
COPY . .

# Crear usuario no-root
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app

# Copiar script de entrada
RUN mkdir -p /app/scripts
COPY --chown=appuser:appuser scripts/entrypoint.sh /app/scripts/entrypoint.sh
RUN chmod +x /app/scripts/entrypoint.sh

# Cambiar al usuario no-root
USER appuser

EXPOSE 8000

# Usar el script de entrada
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]