from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
import types
import sys

from pydantic import BaseModel

# Stub minimal modules to satisfy imports without requiring full app
auth_module = types.ModuleType("open_webui.utils.auth")

class DummyUser(BaseModel):
    id: str = "1"
    name: str = "Test"
    email: str = "test@example.com"
    role: str = "admin"


async def get_admin_user():
    return DummyUser()


async def get_verified_user():
    return DummyUser()


auth_module.get_admin_user = get_admin_user
auth_module.get_verified_user = get_verified_user
sys.modules["open_webui.utils.auth"] = auth_module

config_module = types.ModuleType("open_webui.config")


def get_config():
    return {}


def save_config(config):
    return config


class BannerModel(BaseModel):
    id: str
    type: str
    title: str | None = None
    content: str = ""
    dismissible: bool = True
    timestamp: int = 0


config_module.get_config = get_config
config_module.save_config = save_config
config_module.BannerModel = BannerModel
sys.modules["open_webui.config"] = config_module

env_module = types.ModuleType("open_webui.env")
env_module.SRC_LOG_LEVELS = {"CONFIG": "INFO"}
sys.modules["open_webui.env"] = env_module

from open_webui.routers import configs as configs_router


def create_app():
    app = FastAPI()
    app.include_router(configs_router.router, prefix="/configs")
    app.state.config = SimpleNamespace(
        DEFAULT_MODELS=None,
        MODEL_ORDER_LIST=None,
        MODEL_FALLBACK_PRIORITIES=None,
    )
    return app


def test_set_models_config_with_list():
    app = create_app()
    client = TestClient(app)
    payload = {
        "DEFAULT_MODELS": ["m1", "m2"],
        "MODEL_FALLBACK_PRIORITIES": ["m2", "m1"],
        "MODEL_ORDER_LIST": ["m1", "m2"],
    }
    response = client.post("/configs/models", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["DEFAULT_MODELS"] == ["m1", "m2"]
    assert data["MODEL_FALLBACK_PRIORITIES"] == ["m2", "m1"]

    response = client.get("/configs/models")
    assert response.status_code == 200
    data = response.json()
    assert data["DEFAULT_MODELS"] == ["m1", "m2"]


def test_set_models_config_with_string():
    app = create_app()
    client = TestClient(app)
    payload = {
        "DEFAULT_MODELS": "x,y",
        "MODEL_FALLBACK_PRIORITIES": "y,x",
        "MODEL_ORDER_LIST": [],
    }
    response = client.post("/configs/models", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["DEFAULT_MODELS"] == "x,y"
    assert data["MODEL_FALLBACK_PRIORITIES"] == "y,x"


def test_set_models_config_invalid_payload():
    app = create_app()
    client = TestClient(app)
    payload = {
        "DEFAULT_MODELS": 123,
        "MODEL_ORDER_LIST": 456,
    }
    response = client.post("/configs/models", json=payload)
    assert response.status_code == 422
