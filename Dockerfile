FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements/runtime.txt requirements/runtime.txt
RUN pip install --no-cache-dir -r requirements/runtime.txt

COPY slgbot/ slgbot/

RUN mkdir -p /app/data/groups /app/data/archive /app/data/runtime \
	&& groupadd --gid 10001 appuser \
	&& useradd --create-home --uid 10001 --gid 10001 appuser \
	&& chown -R appuser:appuser /app

USER appuser

CMD ["python", "-m", "slgbot"]
