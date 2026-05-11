# SLG Bot Slim Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the current ATB bot into a SherLegal-focused group logger with after-hours appeal detection and minimal admin controls.

**Architecture:** Keep Pyrogram and the existing MySQL tables, but replace the oversized `bot.py` runtime with focused handlers. Put configuration parsing in `settings.py`, pure appeal logic in `appeals.py`, and ChatGPT business-message classification in a reduced `chatgpt.py`.

**Tech Stack:** Python, Pyrogram, aiomysql, python-dotenv, OpenAI Async API, pytest.

---

### Task 1: Configuration And Pure Appeal Rules

**Files:**
- Create: `settings.py`
- Create: `appeals.py`
- Test: `tests/test_settings.py`
- Test: `tests/test_appeals.py`

- [ ] Write tests for env parsing, staff marker matching, working time, and appeal decisions.
- [ ] Run `python -m pytest tests/test_settings.py tests/test_appeals.py -v` and verify failures because modules do not exist.
- [ ] Implement `Settings`, env helpers, staff detection, working-time detection, and `should_handle_appeal`.
- [ ] Re-run the same tests and verify they pass.

### Task 2: Telegram Client And HTML Logging Configuration

**Files:**
- Modify: `bot_settings.py`
- Modify: `chat_to_html.py`
- Test: `tests/test_chat_to_html.py`

- [ ] Write tests that verify HTML asset paths come from configurable project paths and that chat titles are sanitized for filesystem usage.
- [ ] Run `python -m pytest tests/test_chat_to_html.py -v` and verify failures against hard-coded `/home/anik/atbconsultbot`.
- [ ] Move Telegram credentials to `.env` in `bot_settings.py`.
- [ ] Move HTML source paths and group export paths to `settings.py` in `chat_to_html.py`.
- [ ] Re-run the test and verify it passes.

### Task 3: Database Surface

**Files:**
- Modify: `db_functions.py`
- Test: `tests/test_db_functions_static.py`

- [ ] Write a static test that ensures `db_functions.py` no longer imports Bitrix/API client helpers.
- [ ] Run the static test and verify it fails.
- [ ] Keep only group/admin/state/appeal functions in `db_functions.py`.
- [ ] Re-run the static test and verify it passes.

### Task 4: Slim Bot Handlers

**Files:**
- Replace: `bot.py`
- Test: `tests/test_bot_static.py`

- [ ] Write static tests that fail while `bot.py` still imports Bitrix, pandas, reports, requests, or registers removed handlers.
- [ ] Replace `bot.py` with slim handlers for admin menu, group tracking, log recording, auto-reply, appeal list sending, log archive, callback handling, and scheduler.
- [ ] Re-run static tests and pure unit tests.

### Task 5: Environment Example And Verification

**Files:**
- Create: `.env.example`

- [ ] Add a SherLegal `.env.example` with all configurable keys and safe placeholder values.
- [ ] Run `python -m compileall .` to verify syntax.
- [ ] Run `python -m pytest -v` if pytest is available.
- [ ] Report any commands that cannot run because dependencies are missing.
