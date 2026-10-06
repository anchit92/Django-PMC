import logging
import threading
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .runner import run_scheduled_tasks

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def alb_health_check(request):
    """
    AWS ALB Health Check endpoint.
    Spawns run_scheduled_tasks() in a non-blocking background thread
    and immediately returns HttpResponse("OK") to ALB.
    """
    try:
        thread = threading.Thread(
            target=run_scheduled_tasks,
            name="django-pmc-scheduled-task-runner",
            daemon=True
        )
        thread.start()
    except Exception as exc:
        logger.error(f"[django_PMC] Failed to launch scheduled tasks thread: {exc}", exc_info=True)

    return HttpResponse("OK", content_type="text/plain", status=200)
