"""Bounded HTTP client; no database writes until a complete image is validated."""
from io import BytesIO
import requests
from PIL import Image, ImageOps, UnidentifiedImageError
from django.conf import settings


class ColorizationError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def colorize(original):
    original = bytes(original)
    if len(original) > settings.COLORIZATION_MAX_BYTES:
        raise ColorizationError('input_too_large')
    try:
        with Image.open(BytesIO(original)) as image:
            if image.width * image.height > settings.COLORIZATION_MAX_PIXELS:
                raise ColorizationError('input_too_large')
            expected_size = ImageOps.exif_transpose(image).size
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ColorizationError('invalid_input')
    try:
        with requests.post(
            settings.DDCOLOR_URL.rstrip('/') + '/upload-image/',
            files={'image': ('original', original, 'application/octet-stream')},
            timeout=(settings.DDCOLOR_CONNECT_TIMEOUT, settings.DDCOLOR_READ_TIMEOUT),
            stream=True,
        ) as response:
            if response.status_code != 200:
                raise ColorizationError('service_unavailable' if response.status_code >= 500 else 'service_rejected')
            if response.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'image/jpeg':
                raise ColorizationError('invalid_response')
            data = bytearray()
            for chunk in response.iter_content(65536):
                data.extend(chunk)
                if len(data) > settings.COLORIZATION_MAX_BYTES:
                    raise ColorizationError('output_too_large')
            model = response.headers.get('X-Colorization-Model', 'unknown')[:255]
    except requests.Timeout:
        raise ColorizationError('timeout')
    except requests.RequestException:
        raise ColorizationError('service_unavailable')
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format != 'JPEG' or image.size != expected_size:
                raise ColorizationError('invalid_response')
            image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ColorizationError('invalid_response')
    return bytes(data), model
