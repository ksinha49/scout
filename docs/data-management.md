# Data Management

## Collection Namespaces

Vector collections are separated into namespaces to prevent data from mixing:

- `user-<user_id>` – personal vectors for each user.
- `kb-{kb_name}-{kb_id}` – vectors belonging to a knowledge base. `{kb_name}` is a slugified name and `{kb_id}` is the unique identifier.

## CRUD Examples

### User Namespace

#### Create

```json
POST /retrieval/process/file
{
  "file_id": "<file_uuid>",
  "collection_name": "user-<user_id>"
}
```

#### Read

```json
POST /retrieval/query/collection
{
  "collection_name": "user-<user_id>",
  "query": "setup steps"
}
```

#### Update

```json
POST /retrieval/process/file
{
  "file_id": "<file_uuid>",
  "collection_name": "user-<user_id>",
  "content": "<new content>"
}
```

#### Delete

```json
POST /retrieval/delete
{
  "collection_name": "user-<user_id>",
  "file_id": "<file_uuid>"
}
```

### Knowledge Base Namespace

#### Create

```json
POST /retrieval/process/file
{
  "file_id": "<file_uuid>",
  "collection_name": "kb-{kb_name}-{kb_id}"
}
```

#### Read

```json
POST /retrieval/query/collection
{
  "collection_name": "kb-{kb_name}-{kb_id}",
  "query": "deployment guide"
}
```

#### Update

```json
POST /retrieval/process/file
{
  "file_id": "<file_uuid>",
  "collection_name": "kb-{kb_name}-{kb_id}",
  "content": "<updated text>"
}
```

#### Delete

```json
POST /retrieval/delete
{
  "collection_name": "kb-{kb_name}-{kb_id}",
  "file_id": "<file_uuid>"
}
```

## Metadata Filters

Documents inserted into a collection include metadata fields such as:

- `file_id` – the identifier of the uploaded file
- `session_id` – the chat or session that produced the content (optional)

When querying, you can provide metadata filters to limit the scope of the search. Use the appropriate `collection_name` for the namespace you need.

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
- Removing a file from a knowledge base only deletes the file itself when no other knowledge bases or user collections reference it.
- A periodic task deletes files older than 24 hours that are not attached to any knowledge base and removes their associated vectors from the user collection. Knowledge base collections are not affected by this cleanup.

These features help keep user collections accurate and free of stale data while maintaining persistent knowledge bases.
