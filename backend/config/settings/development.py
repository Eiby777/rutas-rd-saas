from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Base de datos en Docker Compose
DATABASES['default']['HOST'] = env('DB_HOST', default='db')