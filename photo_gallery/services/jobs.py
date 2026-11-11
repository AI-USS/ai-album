import logging
import uuid
import time
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from photo_gallery.models import ColorizationJob, Photographic
from .colorization import colorize, ColorizationError

logger = logging.getLogger(__name__)


def run_one():
    started = time.monotonic()
    now = timezone.now()
    with transaction.atomic():
        # Reclaim only expired reservations. Tokens fence out late responses.
        expired = ColorizationJob.objects.select_for_update(skip_locked=True).filter(status='running', lease_until__lt=now)
        for job in expired:
            job.status = 'failed' if job.attempts >= settings.COLORIZATION_MAX_ATTEMPTS else 'queued'
            job.error_code = 'worker_expired'
            job.finished_at = now if job.status == 'failed' else None
            job.reservation = None
            job.save()
        job = ColorizationJob.objects.select_for_update(skip_locked=True).filter(status='queued').order_by('created_at', 'pk').first()
        if not job:
            return False
        token = uuid.uuid4()
        job.status = 'running'
        job.started_at = now
        job.lease_until = now + timedelta(seconds=settings.COLORIZATION_LEASE_SECONDS)
        job.reservation = token
        job.attempts += 1
        job.error_code = ''
        job.save()
        job_id, photo_id = job.pk, job.photographic_id
    try:
        original = Photographic.objects.values_list('awers', flat=True).get(pk=photo_id)
        data, model = colorize(original)
        error = ''
    except Photographic.DoesNotExist:
        return True
    except ColorizationError as exc:
        error = exc.code
    except Exception:
        logger.exception('Unexpected colorization error job=%s', job_id)
        error = 'internal_error'
    with transaction.atomic():
        # Same lock order as the start endpoint: photo, then job.
        photo = Photographic.objects.select_for_update().only('id').filter(pk=photo_id).first()
        current = ColorizationJob.objects.select_for_update().filter(pk=job_id, status='running', reservation=token).first()
        if photo is None or current is None:
            return True
        if not error:
            photo.colorized = data
            photo.colorized_model = model
            photo.colorized_at = timezone.now()
            photo.save(update_fields=['colorized', 'colorized_model', 'colorized_at'])
        current.status = 'failed' if error else 'succeeded'
        current.error_code = error
        current.finished_at = timezone.now()
        current.lease_until = None
        current.reservation = None
        current.save()
    logger.info('Colorization job=%s result=%s duration=%.2fs', job_id, error or 'succeeded', time.monotonic() - started)
    return True
