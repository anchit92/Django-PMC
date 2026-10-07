import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.management import call_command
from django.db import DatabaseError, IntegrityError, close_old_connections
from django.utils import timezone

try:
    from croniter import croniter
    HAS_CRONITER = True
except ImportError:
    HAS_CRONITER = False

from .models import TaskLock

logger = logging.getLogger(__name__)


def run_scheduled_tasks():
    """
    Iterates over settings.CRON_TASKS and executes due tasks using atomic DB locking.
    Supports both cron expressions ('cron': '0 3 * * *') and interval schedules ('interval_seconds': 60).
    """
    try:
        cron_tasks = getattr(settings, "CRON_TASKS", {})
        if not cron_tasks:
            logger.debug("[django_PMC] No CRON_TASKS defined in settings.py")
            return

        now = timezone.now()

        for task_name, task_config in cron_tasks.items():
            try:
                command = task_config.get("command")
                cron_expr = task_config.get("cron")
                interval_seconds = task_config.get("interval_seconds")

                if not command:
                    logger.warning(f"[django_PMC] Task '{task_name}' is missing 'command'. Skipping.")
                    continue

                # Calculate next lock time using cron expression or interval seconds
                if cron_expr:
                    if not HAS_CRONITER:
                        logger.error(
                            f"[django_PMC] Task '{task_name}' requires 'croniter' for cron expression '{cron_expr}'. "
                            f"Please install croniter via: pip install croniter"
                        )
                        continue
                    try:
                        next_lock_time = croniter(cron_expr, now).get_next(datetime)
                        if timezone.is_aware(now) and timezone.is_naive(next_lock_time):
                            next_lock_time = timezone.make_aware(next_lock_time, timezone.get_current_timezone())
                    except Exception as cron_err:
                        logger.error(f"[django_PMC] Invalid cron expression '{cron_expr}' for task '{task_name}': {cron_err}")
                        continue
                elif interval_seconds is not None:
                    next_lock_time = now + timedelta(seconds=interval_seconds)
                else:
                    # Default fallback interval: 60 seconds
                    next_lock_time = now + timedelta(seconds=60)

                # Step 1: Ensure lock row exists (ignore IntegrityError/DatabaseError from concurrent creation)
                try:
                    TaskLock.objects.get_or_create(
                        name=task_name,
                        defaults={"locked_until": now}
                    )
                except (IntegrityError, DatabaseError):
                    pass

                # Step 2: Perform atomic database update to acquire lock
                try:
                    lock_acquired = TaskLock.objects.filter(
                        name=task_name,
                        locked_until__lte=now
                    ).update(locked_until=next_lock_time)
                except DatabaseError as db_err:
                    logger.debug(f"[django_PMC] DB contention acquiring lock for '{task_name}': {db_err}")
                    lock_acquired = 0



                # Step 3: If update returns 1, lock acquired -> execute management command
                if lock_acquired == 1:
                    logger.info(f"[django_PMC] Lock acquired for task '{task_name}'. Running: {command}")
                    try:
                        if isinstance(command, (list, tuple)):
                            cmd_name = command[0]
                            cmd_args = command[1:]
                            call_command(cmd_name, *cmd_args)
                        elif isinstance(command, dict):
                            cmd_name = command.get("name")
                            cmd_args = command.get("args", [])
                            cmd_kwargs = command.get("kwargs", {})
                            call_command(cmd_name, *cmd_args, **cmd_kwargs)
                        else:
                            call_command(command)
                        logger.info(f"[django_PMC] Task '{task_name}' completed successfully.")
                    except Exception as exc:
                        logger.error(
                            f"[django_PMC] Execution failed for task '{task_name}': {exc}",
                            exc_info=True
                        )
                else:
                    logger.debug(f"[django_PMC] Task '{task_name}' is locked or not due yet.")

            except Exception as task_err:
                logger.error(
                    f"[django_PMC] Unexpected error while processing task '{task_name}': {task_err}",
                    exc_info=True
                )

    finally:
        # Close old DB connections to prevent connection pool exhaustion in background threads
        close_old_connections()
