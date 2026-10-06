from django.test import TestCase
from django.utils import timezone
from django_pmc.models import TaskLock


class TaskLockModelTest(TestCase):
    def test_create_task_lock(self):
        now = timezone.now()
        lock = TaskLock.objects.create(name="test_task", locked_until=now)
        self.assertEqual(lock.name, "test_task")
        self.assertEqual(lock.locked_until, now)
        self.assertIn("test_task", str(lock))

    def test_unique_name_constraint(self):
        TaskLock.objects.create(name="unique_task")
        with self.assertRaises(Exception):
            TaskLock.objects.create(name="unique_task")
