from io import BytesIO
from PIL import Image, UnidentifiedImageError
from django.db import transaction
from django.db.models import BooleanField, Case, Q, When
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from .models import Photographic


def photo_query():
    # Status polling must not transfer full originals/results from PostgreSQL.
    return Photographic.objects.annotate(
        has_result=Case(
            When(Q(colorized__isnull=False) & ~Q(colorized=b''), then=True),
            default=False, output_field=BooleanField(),
        ),
    ).defer('awers', 'rewers', 'colorized')


@require_POST
def start(request, pk):
    # Uses the existing shared-album access policy; CSRF middleware is enabled.
    with transaction.atomic():
        photo = get_object_or_404(photo_query().select_for_update(), pk=pk)
        job = photo.colorization_jobs.filter(status__in=['queued', 'running']).first()
        if not job and photo.has_result and request.POST.get('regenerate') != '1':
            return JsonResponse({'status': 'succeeded', 'has_result': True, 'image_url': reverse('colorized_image', args=[pk])})
        if not job:
            job = photo.colorization_jobs.create()
    return JsonResponse({'job_id': job.pk, 'status': job.status, 'status_url': reverse('colorization_status', args=[pk])}, status=202)


@never_cache
@require_GET
def status(request, pk):
    photo = get_object_or_404(photo_query(), pk=pk)
    job = photo.colorization_jobs.order_by('-pk').first()
    return JsonResponse({
        'job_id': job.pk if job else None,
        'status': job.status if job else ('succeeded' if photo.has_result else 'idle'),
        'error_code': job.error_code if job else '',
        'has_result': photo.has_result,
        'result_version': photo.colorized_at.isoformat() if photo.colorized_at else 'legacy',
        'image_url': reverse('colorized_image', args=[pk]) if photo.has_result else None,
    })


@require_GET
def image(request, pk):
    photo = get_object_or_404(Photographic.objects.only('colorized'), pk=pk)
    if not photo.colorized:
        raise Http404
    # Legacy results have no declared format; inspect them instead of mislabelling.
    try:
        with Image.open(BytesIO(bytes(photo.colorized))) as result:
            mime = Image.MIME.get(result.format, 'application/octet-stream')
            extension = result.format.lower()
    except (UnidentifiedImageError, OSError, ValueError):
        raise Http404
    response = HttpResponse(bytes(photo.colorized), content_type=mime)
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    if request.GET.get('download') == '1':
        response['Content-Disposition'] = f'attachment; filename="photo-{pk}-colorized.{extension}"'
    return response


def source_response(photo, data, kind):
    if not data:
        raise Http404
    try:
        with Image.open(BytesIO(bytes(data))) as result:
            mime = Image.MIME.get(result.format, 'application/octet-stream')
            extension = result.format.lower()
    except (UnidentifiedImageError, OSError, ValueError):
        raise Http404
    response = HttpResponse(bytes(data), content_type=mime)
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response, f'photo-{photo.pk}-{kind}.{extension}'


@require_GET
def source_image(request, pk):
    photo = get_object_or_404(Photographic.objects.only('awers'), pk=pk)
    response, filename = source_response(photo, photo.awers, 'original')
    if request.GET.get('download') == '1':
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@require_GET
def reverse_image(request, pk):
    photo = get_object_or_404(Photographic.objects.only('rewers'), pk=pk)
    response, filename = source_response(photo, photo.rewers, 'reverse')
    if request.GET.get('download') == '1':
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
