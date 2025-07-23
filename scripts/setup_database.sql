-- scripts/setup_database.sql
CREATE DATABASE rutas_rd;
CREATE USER admin WITH PASSWORD 'admin123_rutas_rd_2024';
GRANT ALL PRIVILEGES ON DATABASE rutas_rd TO admin;

-- Extensiones útiles para PostgreSQL
\c rutas_rd
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Para búsquedas de texto
CREATE EXTENSION IF NOT EXISTS "postgis";  -- Para operaciones geoespaciales (opcional)
