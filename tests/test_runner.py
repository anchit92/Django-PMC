from datetime import timedelta
from unittest.mock import patch
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from django_pmc.models import TaskLock
from django_pmc.runner import run_scheduled_tasks


class RunnerTestCase(TransactionTestCase):

    @patch("django_pmc.runner.call_command")
    def test_run_scheduled_tasks_acquires_lock_and_executes(self, mock_call_cmd):
        test_cron_tasks = {
            "test_job": {
                "command": "clearsessions",
                "interval_seconds": 120,
            }
        }
        with override_settings(CRON_TASKS=test_cron_tasks):
            run_scheduled_tasks()

            # Check lock created and locked into the future
            lock = TaskLock.objects.get(name="test_job")
            self.assertGreater(lock.locked_until, timezone.now())
            mock_call_cmd.assert_called_once_with("clearsessions")

    @patch("django_pmc.runner.call_command")
    def test_duplicate_execution_prevented_by_lock(self, mock_call_cmd):
        # Set lock far in the future
        future_time = timezone.now() + timedelta(minutes=10)
        TaskLock.objects.create(name="test_job", locked_until=future_time)

        test_cron_tasks = {
            "test_job": {
                "command": "clearsessions",
                "interval_seconds": 60,
            }
        }
        with override_settings(CRON_TASKS=test_cron_tasks):
            run_scheduled_tasks()
            # Command should not be called because task is currently locked
            mock_call_cmd.assert_not_called()

    @patch("django_pmc.runner.call_command")
    def test_command_failure_does_not_crash_loop(self, mock_call_cmd):
        mock_call_cmd.side_effect = Exception("Command error")

        test_cron_tasks = {
            "failing_job": {
                "command": "bad_command",
                "interval_seconds": 60,
            },
            "succeeding_job": {
                "command": "good_command",
                "interval_seconds": 60,
            }
        }
        with override_settings(CRON_TASKS=test_cron_tasks):
            # Should run without raising exception
            run_scheduled_tasks()
            self.assertEqual(mock_call_cmd.call_count, 2)

    @patch("django_pmc.runner.call_command")
    def test_concurrent_alb_health_checks_prevent_duplicate_runs(self, mock_call_cmd):
        """
        Simulate 5 containers receiving ALB health checks simultaneously.
        Only 1 container should execute the command; the other 4 must skip it.
        """
        import threading

        test_cron_tasks = {
            "concurrent_task": {
                "command": "clearsessions",
                "interval_seconds": 300,
            }
        }

        TaskLock.objects.create(
            name="concurrent_task",
            locked_until=timezone.now() - timedelta(seconds=10)
        )

        threads = []
        with override_settings(CRON_TASKS=test_cron_tasks):
            for i in range(5):
                t = threading.Thread(target=run_scheduled_tasks)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # Ensure call_command was invoked EXACTLY ONCE
            self.assertEqual(mock_call_cmd.call_count, 1)

    @patch("django_pmc.runner.call_command")
    def test_cron_expression_scheduling(self, mock_call_cmd):
        """
        Verify that 5-field cron syntax ('cron': '0 3 * * *') calculates next_lock_time and runs correctly.
        """
        test_cron_tasks = {
            "cron_job": {
                "command": "clearsessions",
                "cron": "0 3 * * *",  # 3:00 AM every day
            }
        }
        with override_settings(CRON_TASKS=test_cron_tasks):
            run_scheduled_tasks()

            mock_call_cmd.assert_called_once_with("clearsessions")
            lock = TaskLock.objects.get(name="cron_job")
            self.assertGreater(lock.locked_until, timezone.now())



