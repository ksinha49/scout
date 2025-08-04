import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[5]
os.environ.setdefault("ALLOWED_MODULES_FILE", str(BACKEND_DIR / "ALLOWED_MODULES.json"))

from open_webui.routers.openai import router as openai_router
from test.util.mock_user import mock_user


class DummyResponse:
    def __init__(self):
        self.status = 200
        self.headers = {"Content-Type": "application/json"}

    async def json(self):
        return {"id": "1", "choices": []}

    def raise_for_status(self):
        pass

    def close(self):
        pass


class DummySession:
    last_request = {}

    def __init__(self, *args, **kwargs):
        pass

    async def request(self, method, url, data=None, headers=None):
        DummySession.last_request = {
            "method": method,
            "url": url,
            "data": data,
            "headers": headers,
        }
        return DummyResponse()

    async def close(self):
        pass


def create_app():
    app = FastAPI()
    app.include_router(openai_router, prefix="/openai")
    app.state.config = SimpleNamespace(
        OPENAI_API_BASE_URLS=["http://mock"],
        OPENAI_API_KEYS=["test"],
        OPENAI_API_CONFIGS={0: {}},
        DEFAULT_MODELS=["fallback-model"],
        MODEL_FALLBACK_PRIORITIES=["fallback-model"],
        ENABLE_OPENAI_API=True,
    )
    return app


def test_retry_on_network_failure():
    app = create_app()
    client = TestClient(app)

    async def mock_get_all_models(request, user=None):
        call = mock_get_all_models.calls
        if call == 0:
            request.app.state.OPENAI_MODELS = {}
        else:
            request.app.state.OPENAI_MODELS = {
                "fallback-model": {"id": "fallback-model", "urlIdx": 0}
            }
        mock_get_all_models.calls += 1
        return {"data": list(request.app.state.OPENAI_MODELS.values())}

    mock_get_all_models.calls = 0

    async def mock_invalidate(request, user=None):
        pass

    mock_get_all_models.invalidate = mock_invalidate

    with mock_user(app, role="admin"):
        with patch(
            "open_webui.routers.openai.get_all_models", mock_get_all_models
        ), patch("open_webui.routers.openai.aiohttp.ClientSession", DummySession):
            response = client.post(
                "/openai/chat/completions",
                json={"model": "missing", "messages": []},
            )

    assert response.status_code == 200
    assert mock_get_all_models.calls == 2
    sent_payload = json.loads(DummySession.last_request["data"])
    assert sent_payload["model"] == "fallback-model"


def test_missing_default_models_error():
    app = create_app()
    app.state.config.DEFAULT_MODELS = None
    app.state.config.MODEL_FALLBACK_PRIORITIES = None
    client = TestClient(app)

    async def mock_get_all_models(request, user=None):
        mock_get_all_models.calls += 1
        request.app.state.OPENAI_MODELS = {}
        return {"data": []}

    mock_get_all_models.calls = 0

    async def mock_invalidate(request, user=None):
        pass

    mock_get_all_models.invalidate = mock_invalidate

    with mock_user(app, role="admin"):
        with patch(
            "open_webui.routers.openai.get_all_models", mock_get_all_models
        ):
            response = client.post(
                "/openai/chat/completions",
                json={"model": "missing", "messages": []},
            )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "No models are available. Please check your configuration or network connection."
    )
    assert mock_get_all_models.calls == 2
