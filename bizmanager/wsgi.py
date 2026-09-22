import os
import shutil
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bizmanager.settings')

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DB = BASE_DIR / 'db.sqlite3'
DST_DB = Path('/tmp/db.sqlite3')

if os.environ.get('VERCEL'):
    try:
        if SRC_DB.exists():
            if DST_DB.exists():
                DST_DB.unlink()
            shutil.copy(SRC_DB, DST_DB)
    except:
        pass

application = get_wsgi_application()

# Fix 500: crée les tables dans /tmp si elles n'existent pas
if os.environ.get('VERCEL'):
    try:
        from django.core.management import call_command
        call_command('migrate', '--noinput', verbosity=0)
    except:
        pass

app = application