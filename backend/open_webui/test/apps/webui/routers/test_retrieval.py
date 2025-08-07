import json
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock

# Ensure env module loads with dictionary configuration before importing open_webui
tmp = tempfile.NamedTemporaryFile(delete=False)
tmp.write(json.dumps({}).encode())
tmp.flush()
os.environ["ALLOWED_MODULES_FILE"] = tmp.name

from test.util.abstract_integration_test import AbstractPostgresTest



class DummyVectorClient:
    def __init__(self):
        self.calls = []

    def query(self, collection_name, filter):
        self.calls.append((collection_name, filter))
        hashes = filter.get("hash", [])
        if isinstance(hashes, list) and hashes:
            # Simulate first hash already existing
            return SimpleNamespace(
                ids=[["dup"]],
                documents=[["dup"]],
                metadatas=[[{"hash": hashes[0]}]],
            )
        return SimpleNamespace(ids=[[]], documents=[[]], metadatas=[[]])


class TestProcessFilesBatch(AbstractPostgresTest):
    BASE_PATH = "/api/v1/retrieval"

    def setup_method(self):
        super().setup_method()
        from open_webui.models.users import Users
        from open_webui.models.files import Files

        self.users = Users
        self.files = Files

        self.user = self.users.insert_new_user(
            id="u1", name="user", email="user@example.com"
        )

    def _create_file(self, id, content):
        from open_webui.models.files import FileForm

        form = FileForm(
            id=id,
            filename=f"{id}.txt",
            path=f"/tmp/{id}.txt",
            data={"content": content},
            meta={},
        )
        return self.files.insert_new_file(self.user.id, form)

    def test_batch_duplicate_lookup_and_empty_skip(self, monkeypatch):
        from open_webui.routers import retrieval
        from open_webui.routers.retrieval import (
            BatchProcessFilesForm,
            process_files_batch,
        )

        file1 = self._create_file("f1", "hello")
        file2 = self._create_file("f2", "hello")
        file3 = self._create_file("f3", "")

        dummy_client = DummyVectorClient()
        monkeypatch.setattr(retrieval, "VECTOR_DB_CLIENT", dummy_client)
        monkeypatch.setattr(retrieval, "save_docs_to_vector_db", lambda **kwargs: None)

        request = MagicMock()
        request.app.state.EMBEDDING_FUNCTION = lambda text, prefix=None: [0.0]

        form = BatchProcessFilesForm(
            files=[file1, file2, file3], collection_name="test_collection"
        )

        resp = process_files_batch(request, form, self.user)

        # Expect one query for both hashes
        assert len(dummy_client.calls) == 1
        assert isinstance(dummy_client.calls[0][1]["hash"], list)
        # Validate statuses
        status_map = {r.file_id: r.status for r in resp.results}
        assert status_map[file1.id] == "skipped_duplicate"
        assert status_map[file2.id] == "completed"
        assert status_map[file3.id] == "skipped_empty"

