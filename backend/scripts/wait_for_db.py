"""Wait briefly for PostgreSQL before running Django startup commands."""
import os
import sys
import time
from pathlib import Path

import django
from django.db import OperationalError, connection

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

MAX_ATTEMPTS = 30
RETRY_DELAY_SECONDS = 1

for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        connection.ensure_connection()
    except OperationalError:
        connection.close()
        print(
            f"PostgreSQL no está disponible (intento {attempt}/{MAX_ATTEMPTS}).",
            flush=True,
        )
        time.sleep(RETRY_DELAY_SECONDS)
    else:
        print("PostgreSQL está disponible.", flush=True)
        connection.close()
        sys.exit(0)

print("No se pudo conectar con PostgreSQL.", file=sys.stderr)
sys.exit(1)
