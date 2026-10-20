# Fitboddy Telegram Bot

Production-ready async Telegram fitness bot scaffold.

Документация монорепо (MkDocs, дорожная карта MVP): в **родительской папке** — `../requirements-docs.txt`, `../mkdocs.yml`, `../docs/`.

## Migrations

Generate a new migration:

```
make migrate-gen
```

Apply migrations:

```
make migrate-up
```

## Workout notification linking

The bot and the plan-service notifications worker must share one bot token. Set `TELEGRAM_BOT_TOKEN` to that token. `BOT_TOKEN` still starts the bot when `TELEGRAM_BOT_TOKEN` is empty, so existing payment notices keep working. If both are set, they must be equal; otherwise the process refuses to start.

The web app issues a code with `POST /api/v1/plans/me/notifications/telegram/link-code`. The user opens `https://t.me/<bot>?start=<code>` or sends `/link <code>`. The bot confirms with:

`POST {PLAN_SERVICE_URL}/api/v1/plans/internal/notifications/telegram`

Header: `X-Service-Token: $INTERNAL_SERVICE_TOKEN`. Body: `{ "code", "chat_id" }`. `PLAN_SERVICE_URL` is the plan-service origin without a path, for example `http://plan-service:8000`. Point it at plan-service itself: the public gateway is expected to reject `/api/v1/plans/internal`.

Replies are short Russian text: the chat is linked, or the code is invalid or expired. If plan-service is not configured or is unreachable, the bot asks to retry later. Empty `PLAN_SERVICE_URL` or `INTERNAL_SERVICE_TOKEN` does not disable payments or `/start`.

There is no `/stop` unlink in the bot. plan-service removes the chat only with `DELETE /api/v1/plans/me/notifications/telegram` and the user's bearer token. It has no internal unlink route for `X-Service-Token`.

| Variable | Purpose |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Same token as the notifications worker. Preferred name. |
| `BOT_TOKEN` | Legacy token name. Used when `TELEGRAM_BOT_TOKEN` is empty. |
| `PLAN_SERVICE_URL` | plan-service origin. Empty disables linking only. |
| `INTERNAL_SERVICE_TOKEN` | Same secret as plan-service. Sent as `X-Service-Token`. |

