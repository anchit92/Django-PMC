SECRET_KEY = "test-secret-key-for-django-pmc"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_pmc",
]

import os
import tempfile

DB_PATH = os.path.join(tempfile.gettempdir(), "django_pmc_test.sqlite3")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DB_PATH,
        "OPTIONS": {
            "timeout": 20,
        },
    }
}


USE_TZ = True
TIME_ZONE = "UTC"

CRON_TASKS = {
    "sample_task": {
        "command": "clearsessions",
        "interval_seconds": 60,
    }
}
