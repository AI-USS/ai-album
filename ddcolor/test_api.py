"""Contract tests use a tiny model double; no weights or torch download needed."""
from io import BytesIO
import sys
import types
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from ddcolor.main import app, lock


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        app.state.colorizer = lambda image: {'output': image}
        self.output_module = types.ModuleType('modelscope.outputs')
        self.output_module.OutputKeys = types.SimpleNamespace(OUTPUT_IMG='output')
        self.patch = patch.dict(sys.modules, {'modelscope.outputs': self.output_module})
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        app.state.colorizer = None

    def data(self):
        data = BytesIO()
        Image.fromarray(np.zeros((6, 8, 3), dtype=np.uint8)).save(data, 'PNG')
        return data.getvalue()

    def test_filename_and_jpeg_contract(self):
        result = self.client.post('/upload-image/', files={'image': ('scan.png', self.data(), 'image/png')})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.headers['content-type'], 'image/jpeg')
        with Image.open(BytesIO(result.content)) as image:
            self.assertEqual(image.size, (8, 6))
            self.assertEqual(image.format, 'JPEG')
        self.assertEqual(self.client.get('/health/ready').status_code, 200)

    def test_invalid_and_oversized_images(self):
        self.assertEqual(self.client.post('/upload-image/', files={'image': ('scan.jpg', b'invalid')}).status_code, 422)
        with patch('ddcolor.main.MAX_BYTES', 2):
            self.assertEqual(self.client.post('/upload-image/', files={'image': ('scan.jpg', self.data())}).status_code, 413)
        with patch('ddcolor.main.MAX_PIXELS', 2):
            self.assertEqual(self.client.post('/upload-image/', files={'image': ('scan.jpg', self.data())}).status_code, 413)

    def test_busy_and_failure_release_lock(self):
        lock.acquire()
        try:
            self.assertEqual(self.client.post('/upload-image/', files={'image': ('a.png', self.data())}).status_code, 503)
        finally:
            lock.release()
        app.state.colorizer = lambda _: 1 / 0
        self.assertEqual(self.client.post('/upload-image/', files={'image': ('a.png', self.data())}).status_code, 500)
        self.assertFalse(lock.locked())

    def test_exif_orientation_is_applied(self):
        stream = BytesIO()
        source = Image.new('RGB', (8, 6), 'gray')
        exif = source.getexif()
        exif[274] = 6
        source.save(stream, 'JPEG', exif=exif)
        result = self.client.post('/upload-image/', files={'image': ('rotated.jpg', stream.getvalue())})
        self.assertEqual(result.status_code, 200)
        with Image.open(BytesIO(result.content)) as output:
            self.assertEqual(output.size, (6, 8))


class ModelLoadingTests(unittest.TestCase):
    def test_huggingface_snapshot_is_passed_as_local_path(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock
        from ddcolor.main import load_colorizer, MODEL, MODEL_REVISION
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / 'resolved-commit'
            snapshot.mkdir()
            (snapshot / 'configuration.json').write_text('{}')
            (snapshot / 'pytorch_model.pt').write_bytes(b'test')
            hub = types.ModuleType('huggingface_hub')
            hub.snapshot_download = Mock(return_value=str(snapshot))
            pipelines = types.ModuleType('modelscope.pipelines')
            pipelines.pipeline = Mock()
            with patch.dict(sys.modules, {'huggingface_hub': hub, 'modelscope.pipelines': pipelines}):
                colorizer, model_id = load_colorizer()
            hub.snapshot_download.assert_called_once_with(repo_id=MODEL, revision=MODEL_REVISION, allow_patterns=['configuration.json', 'pytorch_model.pt'])
            pipelines.pipeline.assert_called_once_with(model=str(snapshot), device='cpu', task='image-colorization')
            self.assertIs(colorizer, pipelines.pipeline.return_value)
            self.assertEqual(model_id, f'{MODEL}@resolved-commit')

    def test_missing_weights_fail_before_pipeline_initialization(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock
        from ddcolor.main import load_colorizer
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'configuration.json').write_text('{}')
            hub = types.ModuleType('huggingface_hub')
            hub.snapshot_download = Mock(return_value=directory)
            pipelines = types.ModuleType('modelscope.pipelines')
            pipelines.pipeline = Mock()
            with patch.dict(sys.modules, {'huggingface_hub': hub, 'modelscope.pipelines': pipelines}):
                with self.assertRaisesRegex(FileNotFoundError, 'pytorch_model.pt'):
                    load_colorizer()
            pipelines.pipeline.assert_not_called()
