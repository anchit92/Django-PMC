import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TaskLock",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        db_index=True,
                        help_text="Unique identifier for the scheduled task",
                        max_length=255,
                        unique=True,
                    ),
                ),
                (
                    "locked_until",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        help_text="Timestamp until which the task execution is locked",
                    ),
                ),
            ],
            options={
                "verbose_name": "Task Lock",
                "verbose_name_plural": "Task Locks",
                "ordering": ["name"],
            },
        ),
    ]
