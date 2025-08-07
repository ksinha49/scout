import logging
import types
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

# Stub modules to avoid heavy dependencies during import
config_stub = types.ModuleType("open_webui.config")
config_stub.VECTOR_DB = None
config_stub.RAG_EMBEDDING_QUERY_PREFIX = ""
config_stub.RAG_EMBEDDING_CONTENT_PREFIX = ""
config_stub.RAG_EMBEDDING_PREFIX_FIELD_NAME = ""
sys.modules["open_webui.config"] = config_stub

env_stub = types.ModuleType("open_webui.env")
env_stub.SRC_LOG_LEVELS = {"RAG": "DEBUG"}
env_stub.OFFLINE_MODE = False
env_stub.ENABLE_FORWARD_USER_INFO_HEADERS = False
sys.modules["open_webui.env"] = env_stub

models_pkg = types.ModuleType("open_webui.models")
sys.modules["open_webui.models"] = models_pkg

users_stub = types.ModuleType("open_webui.models.users")
class UserModel:
    pass
users_stub.UserModel = UserModel
sys.modules["open_webui.models.users"] = users_stub

files_stub = types.ModuleType("open_webui.models.files")
class Files:
    @staticmethod
    def get_file_by_id(file_id):
        return None
files_stub.Files = Files
sys.modules["open_webui.models.files"] = files_stub

utils_pkg = types.ModuleType("open_webui.utils")
sys.modules["open_webui.utils"] = utils_pkg

collections_stub = types.ModuleType("open_webui.utils.collections")
def build_user_collection_name(user_id):
    return f"user_{user_id}"
collections_stub.build_user_collection_name = build_user_collection_name
sys.modules["open_webui.utils.collections"] = collections_stub

connector_stub = types.ModuleType("open_webui.retrieval.vector.connector")
connector_stub.VECTOR_DB_CLIENT = None
sys.modules["open_webui.retrieval.vector.connector"] = connector_stub

vector_main_stub = types.ModuleType("open_webui.retrieval.vector.main")
class GetResult:
    pass
class SearchResult:
    pass
vector_main_stub.GetResult = GetResult
vector_main_stub.SearchResult = SearchResult
sys.modules["open_webui.retrieval.vector.main"] = vector_main_stub

from open_webui.retrieval.utils import get_sources_from_files


def test_get_sources_from_files_debug_logging_no_exception(caplog):
    dummy_request = types.SimpleNamespace(app=None)
    files = [
        {
            "docs": [
                {"content": "hello", "metadata": {"k": "v"}},
            ],
            "file": {"name": "dummy"},
            "id": "1",
            "name": "dummy",
        }
    ]

    with caplog.at_level(logging.DEBUG):
        sources = get_sources_from_files(
            dummy_request,
            files,
            queries=[],
            embedding_function=None,
            k=1,
            reranking_function=None,
            k_reranker=1,
            r=1,
            hybrid_search=False,
        )

    assert sources
    assert any("contexts" in record.message for record in caplog.records)
