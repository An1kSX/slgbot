# Docker Launch

1. Copy `.env.example` to `.env` and fill real Telegram, MySQL, OpenAI, and admin values.
2. Set strong database passwords:
   - `MYSQL_ROOT_PASSWORD`
   - `MYSQL_PASSWORD`
3. Start services:

```bash
docker compose up -d --build
```

4. View bot logs:

```bash
docker compose logs -f bot
```

5. Stop services:

```bash
docker compose down
```

Persistent data:

- MySQL data is stored in Docker volume `mysql_data`.
- Chat logs are stored in `./groups`.
- Archived logs are stored in `./archive`.
- Pyrogram session, runtime settings, and bot log file are stored in `./runtime`.
