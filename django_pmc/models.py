from django.db import models
from django.utils import timezone


class TaskLock(models.Model):
    """
    Model for storing database-backed locks for scheduled tasks.
    Prevents duplicate task execution in multi-container / EC2 ALB environments.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique identifier for the scheduled task"
    )
    locked_until = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Timestamp until which the task execution is locked"
    )

    class Meta:
        verbose_name = "Task Lock"
        verbose_name_plural = "Task Locks"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (locked until {self.locked_until})"
