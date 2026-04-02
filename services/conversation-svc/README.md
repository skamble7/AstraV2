# conversation-svc

Microservice for managing conversations in the ASTRA platform. Handles creation, retrieval, updating, and soft-deletion of conversations along with their message histories. Publishes domain events to RabbitMQ for downstream consumers.

**Port**: 9029

---

## Tech Stack

| Component | Library |
|-----------|---------|
| Framework | FastAPI 0.115+ |
| Server | Uvicorn (ASGI) |
| Database | MongoDB via Motor 3.5+ (async) |
| Validation | Pydantic 2.8+ |
| Message Queue | RabbitMQ via aio-pika 9.4+ |
| Python | 3.11+ |

---

## Configuration

All configuration is environment-based (Pydantic Settings). See [.env.example](.env.example).

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB` | `astra` | MongoDB database name |
| `RABBITMQ_URI` | `amqp://raina:raina@localhost:5672/` | RabbitMQ connection string |
| `RABBITMQ_EXCHANGE` | `raina.events` | RabbitMQ topic exchange name |
| `EVENTS_ORG` | `astra` | Org prefix for event routing keys |
| `SERVICE_NAME` | `conversation-svc` | Service identifier |
| `RELOAD` | `0` | Enable Uvicorn hot-reload (dev only) |

---

## Data Models

All models are defined in [app/models/conversation_models.py](app/models/conversation_models.py).

### `AnthropicMessage`

Represents a single turn in a conversation, compatible with the Anthropic SDK message format.

| Field | Type | Description |
|-------|------|-------------|
| `role` | `"user" \| "assistant"` | Message author |
| `content` | `Any` | Message body — string or structured Anthropic content blocks |

### `ConversationDocument`

The canonical MongoDB document returned by all read and write operations.

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | `str` | Unique conversation identifier |
| `workspace_id` | `str` | Owning workspace |
| `user_id` | `str` | Owning user — required filter key for list queries |
| `name` | `str \| None` | Human-readable conversation name |
| `messages` | `List[AnthropicMessage]` | Full conversation history |
| `reasoning_trace` | `list[dict]` | Internal only — never returned via API |
| `message_count` | `int` | Denormalised count — always updated via `$inc` |
| `deleted_at` | `datetime \| None` | Soft-delete timestamp |
| `created_at` | `datetime` | UTC timestamp — set on creation |
| `updated_at` | `datetime` | UTC timestamp — updated on every write |

### Request / Response Models

| Model | Fields | Used By |
|-------|--------|---------|
| `ConversationCreate` | `workspace_id`, `user_id` (required), `conversation_id` (optional, auto-UUID4), `name` (optional) | `POST /conversations` |
| `ConversationUpdate` | `name: str` | `PATCH /conversations/{id}` |
| `ConversationAppendRequest` | `messages: List[AnthropicMessage]` (min 1), `reasoning_trace: list[dict]` | `PATCH /conversations/{id}/messages` |
| `ConversationReplace` | `messages: List[AnthropicMessage]` | `PUT /conversations/{id}/messages` |
| `ConversationListResponse` | `conversations: list[ConversationDocument]`, `next_cursor: str \| None` | `GET /conversations` |
| `RawMessagesResponse` | `conversation_id: str`, `messages: list[dict]` | `GET /conversations/{id}/messages` |
| `RenderedMessage` | `role: str`, `content: str` | Embedded in `GET /conversations/{id}` response |

---

## API Endpoints

All conversation routes are prefixed with `/conversations`.

### `GET /`
Returns service metadata (name, status, docs URL).

### `GET /health`
Health check endpoint.

**Response** `200`
```json
{ "status": "ok" }
```

---

### `POST /conversations`
Create a new conversation.

**Query params**: `actor` (optional, for audit trail)

**Request body**: `ConversationCreate`
```json
{
  "workspace_id": "ws-123",
  "user_id": "user-456",
  "conversation_id": "optional-custom-id",
  "name": "My Conversation"
}
```

**Response** `201`: `ConversationDocument`

Publishes `conversation.created` event to RabbitMQ.

---

### `GET /conversations`
List conversations for a workspace+user, sorted by `updated_at` descending. Soft-deleted conversations are excluded.

**Query params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `workspace_id` | `str` | required | Filter by workspace |
| `user_id` | `str` | required | Filter by user |
| `limit` | `int` | `20` | Max results (1–200) |
| `before` | `str` | — | Cursor — ISO `updated_at` timestamp from previous page's `next_cursor` |

**Response** `200`: `ConversationListResponse` — `messages` and `reasoning_trace` are excluded from each item.

---

### `GET /conversations/{conversation_id}`
Retrieve a single conversation. Raw `messages` and `reasoning_trace` are excluded; rendered messages are included instead.

**Response** `200`
```json
{
  "conversation_id": "...",
  "workspace_id": "...",
  "user_id": "...",
  "name": "...",
  "message_count": 4,
  "rendered_messages": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Hi there!" }
  ],
  ...
}
```
**Response** `404`: conversation not found

---

### `GET /conversations/{conversation_id}/messages`
Retrieve the raw Anthropic message array for a conversation (for agent replay). Soft-deleted conversations return 404.

**Response** `200`: `RawMessagesResponse`
```json
{
  "conversation_id": "...",
  "messages": [
    { "role": "user", "content": "Hello" }
  ]
}
```
**Response** `404`: conversation not found

---

### `PATCH /conversations/{conversation_id}`
Rename a conversation.

**Request body**: `ConversationUpdate`
```json
{ "name": "New Name" }
```

**Response** `200`: updated `ConversationDocument`
**Response** `404`: conversation not found

---

### `PATCH /conversations/{conversation_id}/messages`
Append messages to a conversation's history. Atomically `$push`es messages and increments `message_count`.

**Request body**: `ConversationAppendRequest`
```json
{
  "messages": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Hi there!" }
  ],
  "reasoning_trace": []
}
```

**Response** `200`: updated `ConversationDocument`
**Response** `404`: conversation not found

---

### `PUT /conversations/{conversation_id}/messages`
Replace the entire message history of a conversation.

**Request body**: `ConversationReplace`
```json
{
  "messages": [
    { "role": "user", "content": "Start over" }
  ]
}
```

**Response** `200`: updated `ConversationDocument`
**Response** `404`: conversation not found

---

### `DELETE /conversations/{conversation_id}`
Soft-delete a conversation (sets `deleted_at`). The record remains in MongoDB but is excluded from all queries.

**Query params**: `actor` (optional)

**Response** `200`
```json
{ "deleted": true }
```
**Response** `404`: conversation not found

Publishes `conversation.deleted` event to RabbitMQ.

---

## Database

**MongoDB** — schemaless document store, no migrations.

**Collection**: `conversations`

**Indexes** (created on startup via `init_indexes()`):

| Field(s) | Type |
|----------|------|
| `conversation_id` | Unique |
| `workspace_id` | Standard |
| `created_at` | Standard |
| `(workspace_id, user_id, updated_at)` | Compound — list queries |
| `deleted_at` | Sparse |

All write operations use `find_one_and_update` with `ReturnDocument.AFTER` for atomic consistency.

---

## Events (RabbitMQ)

The service publishes to a TOPIC exchange (`RABBITMQ_EXCHANGE`). Routing key format:

```
<org>.<service>.<event>.<version>
# e.g. astra.conversation.created.v1
```

| Event | Trigger | Payload |
|-------|---------|---------|
| `conversation.created` | Successful conversation creation | `{ conversation_id, workspace_id, by: actor }` |
| `conversation.deleted` | Successful soft-delete | `{ conversation_id, by: actor }` |

RabbitMQ is optional — if the connection fails at startup the service continues to run (warning logged). Individual publish failures are silently ignored.

---

## Middleware

| Middleware | Behaviour |
|-----------|-----------|
| **CORS** | Allow all origins, methods, and headers |
| **Request Logging** | Logs method, path, status code, and duration (ms) for every request |
| **Error Handlers** | JSON responses for `HTTPException`, Pydantic `ValidationError` (422), and uncaught exceptions (500) |

Authentication is **not** handled by this service — it assumes an upstream API gateway or auth proxy.

---

## Project Structure

```
app/
├── main.py                        # FastAPI app, lifespan startup/shutdown
├── config.py                      # Environment-based settings
├── logging_conf.py                # Console logger setup
├── models/
│   └── conversation_models.py     # Pydantic schemas
├── db/
│   └── mongo.py                   # MongoDB singleton client + index init
├── dal/
│   └── conversation_dal.py        # CRUD operations against MongoDB
├── services/
│   └── conversation_service.py    # Business logic + event publishing + strip_to_rendered
├── routers/
│   ├── health_router.py           # GET /health
│   └── conversation_router.py     # All /conversations routes
├── middleware/
│   ├── cors.py
│   ├── logging.py
│   └── error_handlers.py
└── events/
    └── rabbit.py                  # RabbitMQ bus singleton + publish helper
```

---

## Running Locally

```bash
# Install dependencies
pip install -e .

# Copy and edit environment
cp .env.example .env

# Start the service
uvicorn app.main:app --port 9029 --reload
```

API docs available at `http://localhost:9029/docs`.

## Docker

```bash
docker build -t conversation-svc .
docker run -p 9029:9029 --env-file .env conversation-svc
```
