import logging
from datetime import timedelta
from django.conf import settings
from django.core.management import call_command
from django.db import DatabaseError, IntegrityError, close_old_connections
from django.utils import timezone

from .models import TaskLock

logger = logging.getLogger(__name__)


def run_scheduled_tasks():
    """
    Iterates over settings.CRON_TASKS and executes due tasks using atomic DB locking.
    Prevents duplicate task execution across multiple ALB health checks / containers.
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
                interval_seconds = task_config.get("interval_seconds", 60)

                if not command:
                    logger.warning(f"[django_PMC] Task '{task_name}' is missing 'command'. Skipping.")
                    continue

                # Step 1: Ensure lock row exists (ignore IntegrityError/DatabaseError from concurrent creation)
                try:
                    TaskLock.objects.get_or_create(
                        name=task_name,
                        defaults={"locked_until": now}
                    )
                except (IntegrityError, DatabaseError):
                    pass

                # Step 2: Perform atomic database update to acquire lock
                next_lock_time = now + timedelta(seconds=interval_seconds)
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
