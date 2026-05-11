# SLG Bot Slim Design

## Scope

Adapt the existing ATB bot for SherLegal by keeping only group chat tracking, chat log export, after-hours appeal detection, auto-replies, and admin visibility into chats with appeals.

## Kept Behavior

- Register Telegram groups where the bot is added.
- Update stored group title when the Telegram chat title changes.
- Remove a group from storage when the bot leaves it.
- Log group text messages, photos, and documents to JSON and HTML exports.
- Let admins see the list of known chats.
- Let superadmins download archived chat logs.
- Let admins remove the bot from selected chats.
- Detect after-hours client appeals and auto-reply once per configured cooldown.
- Send admins a configured daily list of chats where after-hours appeals were detected.
- Use ChatGPT only to decide whether a client message is business-related.

## Removed Behavior

- Bitrix24 task creation, task checks, feed posts, employee lookup, anniversaries.
- Employee score and motivation commands.
- Mass posting/editing/deleting posts across groups.
- Translation commands and private ChatGPT dialog.
- Tax report parsing and report reminders.
- ATB-specific quick commands, hard-coded chat ids, hard-coded users, and ATB staff detection.

## Configuration

Move deployment-specific values to `.env`:

- Telegram: `API_ID`, `API_HASH`, `BOT_TOKEN`, `SESSION_NAME`, `BOT_USER_ID`, `BOT_USERNAME`.
- Staff detection: `STAFF_MARKER=SLG`, optional comma-separated `STAFF_USERNAMES`, optional `STAFF_USER_IDS`.
- Work schedule: `WORKING_DAYS=0,1,2,3,4,5`, `WORK_START=09:00`, `WORK_END=18:00`.
- Appeal behavior: `APPEAL_AUTO_REPLY`, `APPEAL_COOLDOWN_SECONDS`, `APPEAL_REPORT_TIME`.
- Logging: `GROUPS_DIR`, `LOG_ARCHIVE_DIR`, `HTML_TEMPLATE_DIR`, `MAX_DOCUMENT_MB`, `LOG_ZIP_PREFIX`.
- Admin bootstrap: `SUPERADMIN_IDS`, optional `ADMIN_IDS`.
- ChatGPT: `OPENAI_API_KEY`, `OPENAI_MODEL`.

## Appeal Rules

A message is an appeal candidate when:

- it is in a group;
- it is incoming and not a service message;
- it is from a client, meaning the sender name, username, and Telegram admin title do not contain the configured staff marker;
- it arrives outside configured working hours or on a non-working day;
- ChatGPT classifies the text or caption as business-related.

When a candidate is accepted, the bot stores `has_appeal=True` for the group, sends the configured auto-reply, and sets a group cooldown timestamp.

## Persistence

Keep MySQL for existing `groups` and `admins` tables. Only the columns required by the kept behavior are used:

- `groups`: `id`, `name`, `timestp`, `has_appeal`.
- `admins`: `id`, `name`, `superadmin`, `state`, `dialog`.

If configured admin ids are present in `.env`, they are used as an additional admin source so a fresh SLG deployment can be bootstrapped without manual DB edits.

## Testing

Add focused unit tests for:

- environment parsing and default settings;
- staff detection using `SLG` in name, username, or custom title;
- working-time detection for Monday-Saturday 09:00-18:00 and Sunday off;
- appeal decision behavior around work hours, staff users, non-business messages, and cooldown.
