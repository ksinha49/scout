import asyncio
import pytest
import sys
from pathlib import Path
import os
import types
import importlib.util

sys.path.append(str(Path(__file__).resolve().parents[3]))
BACKEND_DIR = Path(__file__).resolve().parents[3]
os.environ.setdefault("ALLOWED_MODULES_FILE", str(BACKEND_DIR / "ALLOWED_MODULES.json"))

def stub_module(name, **attrs):
    module = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(module, k, v)
    sys.modules[name] = module

stub_module("open_webui", __path__=[str(BACKEND_DIR / "open_webui")])
for pkg in ["open_webui.models", "open_webui.socket", "open_webui.routers", "open_webui.utils", "open_webui.retrieval"]:
    stub_module(pkg)

stub_module("open_webui.models.chats", Chats=object)
stub_module("open_webui.models.users", Users=object, UserModel=object)
stub_module(
    "open_webui.socket.main",
    get_event_call=lambda *a, **k: None,
    get_event_emitter=lambda *a, **k: None,
    get_active_status_by_user_id=lambda *a, **k: None,
)
stub_module(
    "open_webui.routers.tasks",
    generate_queries=lambda *a, **k: None,
    generate_title=lambda *a, **k: None,
    generate_image_prompt=lambda *a, **k: None,
    generate_chat_tags=lambda *a, **k: None,
)
stub_module(
    "open_webui.routers.retrieval",
    process_web_search=lambda *a, **k: None,
    SearchForm=object,
)
stub_module(
    "open_webui.routers.images",
    image_generations=lambda *a, **k: None,
    GenerateImageForm=object,
)
stub_module(
    "open_webui.routers.pipelines",
    process_pipeline_inlet_filter=lambda *a, **k: None,
    process_pipeline_outlet_filter=lambda *a, **k: None,
)
stub_module("open_webui.utils.webhook", post_webhook=lambda *a, **k: None)
stub_module("open_webui.models.functions", Functions=object)
stub_module("open_webui.models.models", Models=object)
stub_module("open_webui.retrieval.utils", get_sources_from_files=lambda *a, **k: [])
stub_module("open_webui.utils.chat", generate_chat_completion=lambda *a, **k: None)
stub_module(
    "open_webui.utils.task",
    get_task_model_id=lambda *a, **k: None,
    rag_template=lambda *a, **k: None,
    tools_function_calling_generation_template=lambda *a, **k: None,
)
stub_module(
    "open_webui.utils.misc",
    deep_update=lambda *a, **k: None,
    get_message_list=lambda *a, **k: [],
    add_or_update_system_message=lambda *a, **k: None,
    add_or_update_user_message=lambda *a, **k: None,
    get_last_user_message=lambda *a, **k: None,
    get_last_assistant_message=lambda *a, **k: None,
    prepend_to_first_user_message_content=lambda *a, **k: None,
    convert_logit_bias_input_to_json=lambda *a, **k: None,
)
stub_module("open_webui.utils.tools", get_tools=lambda *a, **k: None)
stub_module("open_webui.utils.plugin", load_function_module_by_id=lambda *a, **k: None)
stub_module(
    "open_webui.utils.filter",
    get_sorted_filter_ids=lambda *a, **k: None,
    process_filter_functions=lambda *a, **k: (None, None),
)
stub_module("open_webui.utils.code_interpreter", execute_code_jupyter=lambda *a, **k: None)
stub_module("open_webui.tasks", create_task=lambda *a, **k: None)
stub_module(
    "open_webui.config",
    CACHE_DIR="",
    DEFAULT_TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE="",
    DEFAULT_CODE_INTERPRETER_PROMPT="",
)
stub_module(
    "open_webui.env",
    SRC_LOG_LEVELS={"MAIN": "DEBUG"},
    GLOBAL_LOG_LEVEL="INFO",
    BYPASS_MODEL_ACCESS_CONTROL=False,
    ENABLE_REALTIME_CHAT_SAVE=False,
)
stub_module("open_webui.constants", TASKS=types.SimpleNamespace(FUNCTION_CALLING=0))
stub_module("open_webui.exceptionutil", getErrorMsg=lambda e: str(e))

spec = importlib.util.spec_from_file_location(
    "open_webui.utils.middleware",
    BACKEND_DIR / "open_webui" / "utils" / "middleware.py",
)
middleware = importlib.util.module_from_spec(spec)
spec.loader.exec_module(middleware)


class MockResponse:
    def __init__(self, lines):
        async def iterator():
            for line in lines:
                yield line
        self.body_iterator = iterator()


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ["asyncio"])
async def test_stream_body_handler_emits_reasoning_blocks():
    lines = [
        b'data: {"choices":[{"delta":{"reasoning_content":"<think>foo"}}]}\n\n',
        b'data: {"choices":[{"delta":{"reasoning_content":" bar</think>"}}]}\n\n',
        b'data: {"choices":[{"delta":{"content":"baz"}}]}\n\n',
        b'data: [DONE]\n\n',
    ]
    response = MockResponse(lines)
    events = []

    async def emitter(event):
        events.append(event)

    await middleware.stream_body_handler(response, emitter)

    reasoning_events = [
        e for e in events if e.get("data", {}).get("done")
    ]
    assert reasoning_events, "No reasoning completion event emitted"
    content = reasoning_events[0]["data"]["content"]
    start = content.find("<think>")
    end = content.find("</think>")
    assert start != -1 and end != -1 and start < end
