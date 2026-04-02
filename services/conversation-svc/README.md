# session-svc

Microservice for managing conversation sessions in the ASTRA platform. Handles creation, retrieval, updating, and deletion of sessions along with their message histories. Publishes domain events to RabbitMQ for downstream consumers.

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
| `SERVICE_NAME` | `session-svc` | Service identifier |
| `RELOAD` | `0` | Enable Uvicorn hot-reload (dev only) |

---

## Data Models

All models are defined in [app/models/session_models.py](app/models/session_models.py).

### `AnthropicMessage`

Represents a single turn in a conversation, compatible with the Anthropic SDK message format.

| Field | Type | Description |
|-------|------|-------------|
| `role` | `"user" \| "assistant"` | Message author |
| `content` | `Any` | Message body — string or structured Anthropic content blocks |

### `SessionDocument`

The canonical MongoDB document returned by all read and write operations.

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | Unique session identifier |
| `workspace_id` | `str` | Owning workspace |
| `name` | `str \| None` | Human-readable session name |
| `messages` | `List[AnthropicMessage]` | Full conversation history |
| `created_at` | `datetime` | UTC timestamp — set on creation |
| `updated_at` | `datetime` | UTC timestamp — updated on every write |

### Request Models

| Model | Fields | Used By |
|-------|--------|---------|
| `SessionCreate` | `workspace_id` (required), `session_id` (optional, auto-UUID4), `name` (optional) | `POST /sessions` |
| `SessionUpdate` | `name: str` | `PATCH /sessions/{id}` |
| `SessionAppend` | `messages: List[AnthropicMessage]` (min 1) | `PATCH /sessions/{id}/messages` |
| `SessionReplace` | `messages: List[AnthropicMessage]` | `PUT /sessions/{id}/messages` |

---

## API Endpoints

All session routes are prefixed with `/sessions`.

### `GET /`
Returns service metadata (name, status, docs URL).

### `GET /health`
Health check endpoint.

**Response** `200`
```json
{ "status": "ok" }
```

---

### `POST /sessions`
Create a new session.

**Query params**: `actor` (optional, for audit trail)

**Request body**: `SessionCreate`
```json
{
  "workspace_id": "ws-123",
  "session_id": "optional-custom-id",
  "name": "My Conversation"
}
```

**Response** `201`: `SessionDocument`

Publishes `session.created` event to RabbitMQ.

---

### `GET /sessions`
List sessions for a workspace, sorted by `created_at` descending.

**Query params**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `workspace_id` | `str` | required | Filter by workspace |
| `limit` | `int` | `50` | Max results (1–200) |
| `offset` | `int` | `0` | Pagination offset |

**Response** `200`: `List[SessionDocument]`

---

### `GET /sessions/{session_id}`
Retrieve a single session.

**Response** `200`: `SessionDocument`
**Response** `404`: session not found

---

### `PATCH /sessions/{session_id}`
Rename a session.

**Request body**: `SessionUpdate`
```json
{ "name": "New Name" }
```

**Response** `200`: updated `SessionDocument`
**Response** `404`: session not found

---

### `PATCH /sessions/{session_id}/messages`
Append messages to a session's history (atomic MongoDB `$push`).

**Request body**: `SessionAppend`
```json
{
  "messages": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Hi there!" }
  ]
}
```

**Response** `200`: updated `SessionDocument`
**Response** `404`: session not found

---

### `PUT /sessions/{session_id}/messages`
Replace the entire message history of a session.

**Request body**: `SessionReplace`
```json
{
  "messages": [
    { "role": "user", "content": "Start over" }
  ]
}
```

**Response** `200`: updated `SessionDocument`
**Response** `404`: session not found

---

### `DELETE /sessions/{session_id}`
Delete a session.

**Query params**: `actor` (optional)

**Response** `200`
```json
{ "deleted": true }
```
**Response** `404`: session not found

Publishes `session.deleted` event to RabbitMQ.

---

## Database

**MongoDB** — schemaless document store, no migrations.

**Collection**: `sessions`

**Indexes** (created on startup via `init_indexes()`):

| Field | Type |
|-------|------|
| `session_id` | Unique |
| `workspace_id` | Standard |
| `created_at` | Standard |

All write operations use `find_one_and_update` with `ReturnDocument.AFTER` for atomic consistency.

---

## Events (RabbitMQ)

The service publishes to a TOPIC exchange (`RABBITMQ_EXCHANGE`). Routing key format:

```
<org>.<service>.<event>.<version>
# e.g. astra.session.created.v1
```

| Event | Trigger | Payload |
|-------|---------|---------|
| `session.created` | Successful session creation | `{ session_id, workspace_id, by: actor }` |
| `session.deleted` | Successful session deletion | `{ session_id, by: actor }` |

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
├── main.py                  # FastAPI app, lifespan startup/shutdown
├── config.py                # Environment-based settings
├── logging_conf.py          # Console logger setup
├── models/
│   └── session_models.py    # Pydantic schemas
├── db/
│   └── mongo.py             # MongoDB singleton client + index init
├── dal/
│   └── session_dal.py       # CRUD operations against MongoDB
├── services/
│   └── session_service.py   # Business logic + event publishing
├── routers/
│   ├── health_router.py     # GET /health
│   └── session_router.py    # All /sessions routes
├── middleware/
│   ├── cors.py
│   ├── logging.py
│   └── error_handlers.py
└── events/
    └── rabbit.py            # RabbitMQ bus singleton + publish helper
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
docker build -t session-svc .
docker run -p 9029:9029 --env-file .env session-svc
```
