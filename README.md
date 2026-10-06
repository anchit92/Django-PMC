# Django-PMC (Poor Man's Cron)

`Django-PMC` is a lightweight, zero-dependency reusable Django application designed to execute scheduled management tasks in multi-container / multi-EC2 environments, triggered automatically by AWS Application Load Balancer (ALB) health checks.

---

## Key Features & Architecture

* **Zero Extra Infrastructure:** No need for Celery, Redis, RabbitMQ, or cron daemons.
* **ALB Health Check Triggered:** Runs automatically whenever AWS ALB pings your application health endpoint.
* **Non-Blocking Execution:** Spawns task execution in a background thread and immediately returns HTTP `200 OK` to ALB so health check thresholds are never delayed.
* **Atomic Database Locking:** Uses `TaskLock.objects.filter(name=..., locked_until__lte=now).update(locked_until=...)` to ensure **only one container executes the task**, even if 50 containers receive the ALB health check at the exact same millisecond.
* **Resilient Loop:** Each command execution is isolated in a `try/except` block so one failing command won't abort the rest of the schedule.
* **DB Connection Pool Leak Prevention:** Includes a `finally` block calling `django.db.close_old_connections()` to clean up background thread DB handles.

---

## Installation & Wiring

### 1. Add `django_pmc` to `INSTALLED_APPS`

In your project's `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'django_pmc',
]
```

### 2. Configure Scheduled Tasks (`CRON_TASKS`)

In `settings.py`, define your schedule dictionary:

```python
CRON_TASKS = {
    'clear_expired_sessions': {
        'command': 'clearsessions',
        'interval_seconds': 3600,  # Run once every hour
    },
    'send_daily_digest': {
        'command': 'send_email_digest',
        'interval_seconds': 86400, # Run once every 24 hours
    },
}
```

### 3. Wire Up URL Routing

In your project's root `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ...
    path('', include('django_pmc.urls')),
]
```

Or target the path explicitly:

```python
from django.urls import path
from django_pmc.views import alb_health_check

urlpatterns = [
    path('health/', alb_health_check, name='alb_health_check'),
]
```

Point your **AWS ALB Target Group Health Check Path** to `/health/` (or whichever path you mapped).

### 4. Run Migrations

Create the `TaskLock` table in your database:

```bash
python manage.py migrate
```

---

## Component Code Overview

### 1. Model (`django_pmc/models.py`)

```python
from django.db import models
from django.utils import timezone

class TaskLock(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    locked_until = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "Task Lock"
        verbose_name_plural = "Task Locks"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (locked until {self.locked_until})"
```

### 2. Task Runner (`django_pmc/runner.py`)

```python
import logging
from datetime import timedelta
from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError, DatabaseError, close_old_connections
from django.utils import timezone
from .models import TaskLock

logger = logging.getLogger(__name__)

def run_scheduled_tasks():
    try:
        cron_tasks = getattr(settings, "CRON_TASKS", {})
        if not cron_tasks:
            return

        now = timezone.now()

        for task_name, task_config in cron_tasks.items():
            try:
                command = task_config.get("command")
                interval_seconds = task_config.get("interval_seconds", 60)

                if not command:
                    continue

                # Ensure lock row exists
                try:
                    TaskLock.objects.get_or_create(name=task_name, defaults={"locked_until": now})
                except (IntegrityError, DatabaseError):
                    pass

                # Atomic lock acquisition attempt
                next_lock_time = now + timedelta(seconds=interval_seconds)
                try:
                    lock_acquired = TaskLock.objects.filter(
                        name=task_name,
                        locked_until__lte=now
                    ).update(locked_until=next_lock_time)
                except DatabaseError:
                    lock_acquired = 0

                if lock_acquired == 1:
                    try:
                        call_command(command)
                    except Exception as exc:
                        logger.error(f"[django_PMC] Execution failed for task '{task_name}': {exc}", exc_info=True)
            except Exception as task_err:
                logger.error(f"[django_PMC] Error processing task '{task_name}': {task_err}", exc_info=True)
    finally:
        close_old_connections()
```

### 3. Health Check View (`django_pmc/views.py`)

```python
import threading
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .runner import run_scheduled_tasks

@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def alb_health_check(request):
    thread = threading.Thread(
        target=run_scheduled_tasks,
        name="django-pmc-runner",
        daemon=True
    )
    thread.start()
    return HttpResponse("OK", content_type="text/plain", status=200)
```

---

## Integrating with `django-watchman`

If you already use **`django-watchman`** (or `django-health-check`) as your ALB health check endpoint (e.g. `GET /watchman/`), you can easily trigger `django_PMC` whenever Watchman receives a ping.

### Option A: Custom Watchman Check (Recommended)

1. Create a check function in your app (e.g., `myapp/healthchecks.py`):

```python
import threading
from django_pmc.runner import run_scheduled_tasks

def pmc_runner_check():
    """
    Custom Watchman check that triggers django_PMC in a background thread.
    Returns {"ok": True} instantly so Watchman health checks stay green.
    """
    thread = threading.Thread(
        target=run_scheduled_tasks,
        name="django-pmc-runner",
        daemon=True
    )
    thread.start()
    
    return {"ok": True}
```

2. Add `pmc_runner_check` to `WATCHMAN_CHECKS` in your `settings.py`:

```python
WATCHMAN_CHECKS = (
    'watchman.checks.databases',
    'watchman.checks.caches',
    'watchman.checks.storage',
    'myapp.healthchecks.pmc_runner_check',  # <-- Triggers django_PMC
)
```

### Option B: Wrap Watchman View in `urls.py`

Alternatively, wrap Watchman's status view directly in `urls.py`:

```python
import threading
from django.urls import path
from watchman.views import status as watchman_status
from django_pmc.runner import run_scheduled_tasks

def watchman_pmc_health_check(request):
    # Spawn PMC task runner in background thread
    threading.Thread(target=run_scheduled_tasks, daemon=True).start()
    
    # Delegate to Watchman view
    return watchman_status(request)

urlpatterns = [
    path('watchman/', watchman_pmc_health_check, name='watchman_health'),
]
```

---

## Testing

Run tests locally:

```bash
python tests/runtests.py
```
