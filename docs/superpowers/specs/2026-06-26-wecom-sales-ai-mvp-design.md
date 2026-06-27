# WeCom Sales AI MVP Design

## Goal

Build a runnable MVP for an enterprise WeChat sidebar sales AI assistant. The app stores text chat records, syncs customer data, generates customer profiles, recommends replies, and leaves official WeCom API credentials and Finance SDK integration points configurable through environment variables.

## Scope

Included:
- FastAPI backend with unified API responses.
- SQLAlchemy models for messages, customers, tags, follow-ups, analysis logs, and sync state.
- Redis-compatible token and analysis caching, with an in-memory fallback for local development.
- WeCom access token, external contact, JS-SDK signature, and chat archive adapter interfaces.
- Customer profile engine with keyword tags, intention scoring, tag de-duplication, and LLM tag merge points.
- LLM analysis service compatible with OpenAI-style DeepSeek and Doubao APIs.
- Vue 3 sidebar H5 with recommendation, profile, and follow-up tabs.
- Docker Compose deployment for backend, frontend, MySQL, Redis, and Nginx.

Deferred:
- Real Finance SDK dynamic library loading is represented by a production adapter stub that fails loudly until the Linux SDK library and credentials are mounted.
- Group chat, non-text messages, automatic sending, social feed automation, and team dashboards are outside MVP.

## Architecture

The backend owns all secrets and integrates with WeCom and LLM providers. The frontend only calls backend APIs and uses the WeCom JS-SDK to detect the current external contact in the real sidebar environment. The archive worker pulls text messages through a pluggable adapter, persists them idempotently by `msg_id`, updates the customer profile, and refreshes cached analysis.

## Data Flow

1. Backend obtains WeCom access tokens per secret type and caches them.
2. Archive worker loads the last `seq`, pulls encrypted messages, decrypts them through the selected archive client, and stores single-chat text messages.
3. Customer sync fetches internal users and external contacts through WeCom API wrappers.
4. Profile engine updates tags and intention level after each customer message.
5. Analysis service loads the latest 20 messages, calls the configured OpenAI-compatible model, validates JSON, and falls back to rule-based replies when the model is unavailable.
6. Sidebar H5 calls `/api/analysis/realtime`, `/api/customer/info`, `/api/chat/history`, and follow-up endpoints.

## Error Handling

External integrations return typed failures instead of crashing request handlers. The LLM service returns deterministic fallback suggestions if upstream calls fail or malformed JSON is returned. The Finance SDK production adapter reports a clear configuration error until the official Linux SDK is installed.

## Testing

Backend unit tests cover profile scoring, tag de-duplication, LLM fallback parsing, response format, and token caching. Frontend build verification checks Vue and TypeScript compilation when dependencies are installed.
