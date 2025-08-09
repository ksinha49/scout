import sys
from types import SimpleNamespace
from contextlib import contextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Provide stub modules to avoid heavy imports
env_stub = SimpleNamespace(SRC_LOG_LEVELS={"CONFIG": "INFO"})
config_stub = SimpleNamespace(
    get_config=lambda: {},
    save_config=lambda cfg: None,
    BannerModel=object,
)
auth_stub = SimpleNamespace(get_admin_user=lambda: None, get_verified_user=lambda: None)

sys.modules['open_webui.env'] = env_stub
sys.modules['open_webui.config'] = config_stub
sys.modules['open_webui.utils.auth'] = auth_stub

from open_webui.routers.configs import router as configs_router


@contextmanager
def mock_admin(app: FastAPI):
    def user():
        return SimpleNamespace(role="admin")

    app.dependency_overrides[auth_stub.get_admin_user] = user
    try:
        yield
    finally:
        app.dependency_overrides = {}


def test_get_models_config_with_invalid_types():
    app = FastAPI()
    app.state.config = SimpleNamespace(
        DEFAULT_MODELS=None,
        MODEL_ORDER_LIST=[],
        MODEL_FALLBACK_PRIORITIES=None,
    )
    app.include_router(configs_router)

    with TestClient(app) as client:
        app.state.config.DEFAULT_MODELS = 123
        app.state.config.MODEL_ORDER_LIST = 123
        app.state.config.MODEL_FALLBACK_PRIORITIES = ["a", 1]

        with mock_admin(app):
            response = client.get("/models")

        assert response.status_code == 200
        data = response.json()
        assert data["DEFAULT_MODELS"] == "123"
        assert data["MODEL_ORDER_LIST"] == []
        assert data["MODEL_FALLBACK_PRIORITIES"] == "['a', 1]"
