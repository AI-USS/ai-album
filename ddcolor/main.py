"""Private DDColor HTTP service. Start one process per model instance."""
from contextlib import asynccontextmanager
from io import BytesIO
import logging
import os
from threading import Lock
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)
MAX_BYTES = int(os.getenv('COLORIZATION_MAX_BYTES', 20 * 1024 * 1024))
MAX_PIXELS = int(os.getenv('COLORIZATION_MAX_PIXELS', 20_000_000))
MODEL = os.getenv('DDCOLOR_MODEL', 'camenduru/cv_ddcolor_image-colorization')
DEFAULT_REVISION = '50bfee609054154de7543fea8c02fc8bbeb8b0b0'
MODEL_REVISION = os.getenv('DDCOLOR_MODEL_REVISION') or DEFAULT_REVISION
lock = Lock()


def load_colorizer():
    from huggingface_hub import snapshot_download
    from modelscope.pipelines import pipeline

    logger.info('Downloading DDColor from Hugging Face: %s@%s', MODEL, MODEL_REVISION)
    model_dir = snapshot_download(
        repo_id=MODEL,
        revision=MODEL_REVISION,
        allow_patterns=['configuration.json', 'pytorch_model.pt'],
    )
    for filename in ('configuration.json', 'pytorch_model.pt'):
        if not (Path(model_dir) / filename).is_file():
            raise FileNotFoundError(f'DDColor snapshot is missing {filename}')
    # A local directory prevents ModelScope from fetching weights from its hub.
    colorizer = pipeline(model=model_dir, device='cpu', task='image-colorization')
    return colorizer, f'{MODEL}@{Path(model_dir).name}'


@asynccontextmanager
async def lifespan(app):
    app.state.colorizer, app.state.model_id = load_colorizer()
    yield
    app.state.colorizer = None


app = FastAPI(lifespan=lifespan)


@app.get('/health/ready')
def ready():
    if not getattr(app.state, 'colorizer', None):
        raise HTTPException(503, 'Model unavailable')
    return {'ready': True, 'model': getattr(app.state, 'model_id', MODEL)}


@app.post('/upload-image/')
def upload_image(image: UploadFile = File(...)):
    data = image.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, 'Image too large')
    try:
        with Image.open(BytesIO(data)) as source:
            if source.width * source.height > MAX_PIXELS:
                raise HTTPException(413, 'Too many pixels')
            if source.format not in ('JPEG', 'PNG', 'TIFF', 'BMP', 'WEBP') or getattr(source, 'n_frames', 1) != 1:
                raise HTTPException(422, 'Unsupported image')
            rgb = ImageOps.exif_transpose(source).convert('RGB')
            img = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(422, 'Invalid image')
    if not getattr(app.state, 'colorizer', None) or not lock.acquire(blocking=False):
        raise HTTPException(503, 'Model unavailable or busy')
    try:
        from modelscope.outputs import OutputKeys
        result = app.state.colorizer(img)[OutputKeys.OUTPUT_IMG]
        if result.shape[:2] != img.shape[:2]:
            raise ValueError('Unexpected output dimensions')
        ok, buffer = cv2.imencode('.jpg', result)
        if not ok:
            raise ValueError('JPEG encoding failed')
        output = buffer.tobytes()
        if len(output) > MAX_BYTES:
            raise ValueError('Output too large')
        return Response(output, media_type='image/jpeg', headers={'X-Colorization-Model': getattr(app.state, 'model_id', f'{MODEL}@{MODEL_REVISION}')})
    except Exception:
        logger.exception('Colorization failed')
        raise HTTPException(500, 'Colorization failed')
    finally:
        lock.release()
