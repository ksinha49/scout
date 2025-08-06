# Data Management

## User Collection Scheme

Each user's uploaded files are stored in a dedicated vector collection named `user-<user_id>`. This isolates data per user and ensures that retrieval queries only search within the owner’s data unless additional knowledge bases are used.

## Metadata Filters

Documents inserted into the collection include metadata fields such as:

- `file_id` – the identifier of the uploaded file
- `session_id` – the chat or session that produced the content (optional)

When querying, you can provide metadata filters to limit the scope of the search.

### Querying specific files or sessions

Query a single file:

```json
POST /retrieval/query/doc
{
  "collection_name": "user-<user_id>",
  "query": "How do I install it?",
  "filter": {"file_id": "<file_uuid>"}
}
```

Restrict results to one session:

```json
POST /retrieval/query/doc
{
  "collection_name": "user-<user_id>",
  "query": "What was my last request?",
  "filter": {"session_id": "<socket_id>"}
}
```

Combine filters when querying a collection:

```json
POST /retrieval/query/collection
{
  "collection_name": "user-<user_id>",
  "query": "setup steps",
  "filters": [
    {"file_id": "<file_uuid>"},
    {"session_id": "<socket_id>"}
  ]
}
```

## Cleanup Behaviour

- Updating a file removes existing vectors for that file before new content is inserted.
- A periodic task deletes files older than 24 hours that are not attached to any knowledge base and removes their associated vectors from the user collection.

These features help keep user collections accurate and free of stale data.
