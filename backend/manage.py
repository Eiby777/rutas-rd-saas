#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path
import dotenv


def main():
    """Run administrative tasks."""
    # Load environment variables from .env file
    env_path = Path(__file__).parent / '.env'
    print(f"Loading environment from: {env_path}")
    dotenv.load_dotenv(dotenv_path=env_path)
    
    # Debug: Print some important environment variables
    print("DEBUG - Environment variables:")
    for var in ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']:
        print(f"{var} = {os.getenv(var, 'NOT SET')}")
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
