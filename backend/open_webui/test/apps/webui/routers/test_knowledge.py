import shutil
import pytest
from test.util.abstract_integration_test import AbstractPostgresTest
from test.util.mock_user import mock_webui_user
from open_webui.utils.collections import (
    build_user_collection_name,
    build_kb_collection_name,
)


DOCKER_AVAILABLE = shutil.which("docker") is not None


@pytest.mark.skipif(
    not DOCKER_AVAILABLE, reason="Docker is required for database integration tests"
)
class TestKnowledge(AbstractPostgresTest):
    BASE_PATH = "/api/v1/knowledge"

    @classmethod
    def setup_class(cls):
        super().setup_class()
        from open_webui.models.files import Files, FileForm
        from open_webui.models.knowledge import Knowledges, KnowledgeForm
        from open_webui.retrieval.vector.main import VectorItem
        from open_webui.retrieval.vector.connector import VECTOR_DB_CLIENT

        cls.files = Files
        cls.FileForm = FileForm
        cls.knowledges = Knowledges
        cls.KnowledgeForm = KnowledgeForm
        cls.VectorItem = VectorItem
        cls.vector_client = VECTOR_DB_CLIENT

    def setup_method(self):
        super().setup_method()
        self.vector_client.reset()

    def teardown_method(self):
        self.vector_client.reset()
        self.files.delete_all_files()
        self.knowledges.delete_all_knowledge()
        super().teardown_method()

    def test_query_by_file_id_returns_relevant_chunks(self):
        user_id = "1"
        collection = build_user_collection_name(user_id)

        items = [
            self.VectorItem(
                id="f1c1",
                text="alpha chunk one",
                vector=[1.0, 0.0],
                metadata={"file_id": "file1"},
            ),
            self.VectorItem(
                id="f1c2",
                text="alpha chunk two",
                vector=[1.0, 1.0],
                metadata={"file_id": "file1"},
            ),
            self.VectorItem(
                id="f2c1",
                text="beta chunk",
                vector=[0.0, 1.0],
                metadata={"file_id": "file2"},
            ),
        ]

        self.vector_client.insert(
            collection_name=collection, items=[item.model_dump() for item in items]
        )

        res1 = self.vector_client.query(
            collection_name=collection, filter={"file_id": "file1"}
        )
        assert res1 is not None
        assert sorted(res1.documents[0]) == ["alpha chunk one", "alpha chunk two"]

        res2 = self.vector_client.query(
            collection_name=collection, filter={"file_id": "file2"}
        )
        assert res2 is not None
        assert res2.documents[0] == ["beta chunk"]

    def test_cleanup_and_knowledge_deletion_drops_collection(self):
        user_id = "1"
        file_id = "file1"

        knowledge = self.knowledges.insert_new_knowledge(
            user_id,
            self.KnowledgeForm(
                name="kb", description="desc", data={"file_ids": [file_id]}
            ),
        )

        self.files.insert_new_file(
            user_id,
            self.FileForm(
                id=file_id,
                filename="file.txt",
                path="/tmp/file.txt",
                data={"content": "hello"},
                meta={},
            ),
        )

        item = self.VectorItem(
            id="chunk1",
            text="hello",
            vector=[0.1, 0.2],
            metadata={"file_id": file_id},
        )
        collection_name = build_kb_collection_name(knowledge.name, knowledge.id)
        self.vector_client.insert(
            collection_name=collection_name, items=[item.model_dump()]
        )

        res_before = self.vector_client.query(
            collection_name=collection_name, filter={"file_id": file_id}
        )
        assert res_before is not None
        assert res_before.documents[0] == ["hello"]

        with mock_webui_user(id=user_id):
            response = self.fast_api_client.post(
                self.create_url(f"/{knowledge.id}/file/remove"),
                json={"file_id": file_id},
            )
        assert response.status_code == 200

        res_after = self.vector_client.query(
            collection_name=collection_name, filter={"file_id": file_id}
        )
        assert res_after is not None
        assert res_after.documents[0] == []
        assert self.files.get_file_by_id(file_id) is None

        with mock_webui_user(id=user_id):
            response = self.fast_api_client.delete(
                self.create_url(f"/{knowledge.id}/delete")
            )
        assert response.status_code == 200
        assert self.knowledges.get_knowledge_by_id(knowledge.id) is None
        assert (
            self.vector_client.has_collection(
                collection_name=build_kb_collection_name(knowledge.name, knowledge.id)
            )
            is False
        )
