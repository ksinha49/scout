import builtins
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import contextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure required env variables are set before importing the router
BACKEND_DIR = Path(__file__).resolve().parents[5]
os.environ.setdefault("ALLOWED_MODULES_FILE", str(BACKEND_DIR / "ALLOWED_MODULES.json"))

from open_webui.routers.audio import router as audio_router
from open_webui.utils.auth import (
    get_admin_user,
    get_current_user,
    get_current_user_by_api_key,
    get_verified_user,
)
from open_webui.models.users import User


@contextmanager
def mock_user(app: FastAPI, **kwargs):
    def create_user():
        user_parameters = {
            "id": "1",
            "name": "John Doe",
            "email": "john.doe@ameritas.com",
            "role": "user",
            "profile_image_url": "/user.png",
            "last_active_at": 1627351200,
            "updated_at": 1627351200,
            "created_at": 162735120,
            **kwargs,
        }
        return User(**user_parameters)

    overrides = {
        get_current_user: create_user,
        get_verified_user: create_user,
        get_admin_user: create_user,
        get_current_user_by_api_key: create_user,
    }
    app.dependency_overrides.update(overrides)
    try:
        yield
    finally:
        for key in overrides:
            app.dependency_overrides.pop(key, None)


class TestAudioRouter:
    def setup_method(self):
        app = FastAPI()
        app.include_router(audio_router, prefix="/api/v1/audio")
        app.state.config = SimpleNamespace(
            TTS_ENGINE="whisperspeech", TTS_MODEL="dummy"
        )
        self.app = app
        self.client = TestClient(app)

    def test_whisperspeech_missing_dependency(self):
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "whisperspeech.pipeline":
                raise ModuleNotFoundError(
                    "No module named 'webdataset'", name="webdataset"
                )
            return original_import(name, *args, **kwargs)

        with mock_user(self.app):
            with patch("builtins.__import__", side_effect=mock_import):
                response = self.client.post(
                    "/api/v1/audio/speech", json={"input": "hello"}
                )
        assert response.status_code == 500
        assert response.json()["detail"] == "Install `webdataset` to use WhisperSpeech"

    def test_whisperspeech_tensor_output_saved(self, tmp_path):
        import numpy as np
        import torch

        class DummyPipe:
            def generate(self, text, speaker=None):
                tensor = torch.tensor([0.1, -0.2])
                if torch.cuda.is_available():
                    tensor = tensor.to("cuda")
                return tensor

        self.app.state.whisperspeech_pipe = DummyPipe()

        written = {}

        def fake_write(path, data, samplerate):
            written["data"] = data
            Path(path).write_bytes(b"")

        with mock_user(self.app):
            with (
                patch("open_webui.routers.audio.SPEECH_CACHE_DIR", tmp_path),
                patch("soundfile.write", side_effect=fake_write),
            ):
                response = self.client.post(
                    "/api/v1/audio/speech", json={"input": "hello"}
                )

        assert response.status_code == 200
        assert isinstance(written["data"], np.ndarray)
