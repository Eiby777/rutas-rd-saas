from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Base de datos local
DATABASES['default']['HOST'] = 'localhost'