from pathlib import Path


def test_dockerfile_runs_bot_with_requirements():
    source = Path("Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.11-slim" in source
    assert "COPY requirements.txt" in source
    assert "pip install --no-cache-dir -r requirements.txt" in source
    assert 'CMD ["python", "bot.py"]' in source


def test_compose_defines_bot_and_mysql_services():
    source = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "mysql:" in source
    assert "image: mysql:8.4" in source
    assert "healthcheck:" in source
    assert "bot:" in source
    assert "depends_on:" in source
    assert "MYSQL_HOST: mysql" in source
    assert "SESSION_NAME: /app/runtime/slgbot" in source
    assert "./groups:/app/groups" in source
    assert "./archive:/app/archive" in source
    assert "./runtime:/app/runtime" in source


def test_requirements_include_runtime_dependencies_only():
    source = Path("requirements.txt").read_text(encoding="utf-8")

    for package in ["pyrogram", "python-dotenv", "aiomysql", "openai"]:
        assert package in source


def test_dockerignore_excludes_runtime_and_secret_files():
    source = Path(".dockerignore").read_text(encoding="utf-8")

    for pattern in [".env", "groups/", "archive/", "runtime/", "*.session", "__pycache__/"]:
        assert pattern in source
