# Development Utilities

## Reasoning Stream Test

A unit test demonstrates how streamed responses containing `<think>` tags are
handled by the middleware. Run the test with:

```bash
pytest backend/open_webui/test/util/test_reasoning_stream.py
```

The test feeds a mock response through `middleware.stream_body_handler` and
asserts that a reasoning block is emitted.

## Developer Reasoning Endpoint

When the application runs with `GLOBAL_LOG_LEVEL=DEBUG`, a developer endpoint is
available for manual verification:

```bash
curl -N http://localhost:8000/dev/reasoning
```

The endpoint streams a canned response containing reasoning content and a final
message, allowing manual inspection of the reasoning block handling.
