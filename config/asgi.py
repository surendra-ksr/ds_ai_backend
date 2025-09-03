"""
ASGI config for the ds_ai_backend project.
"""

import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application

# Add the project's 'apps' directory to the Python path.
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / 'apps'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

application = get_asgi_application()
