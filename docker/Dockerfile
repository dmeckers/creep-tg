FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir watchdog

COPY . .

EXPOSE 3000

CMD ["watchmedo", "auto-restart", "--recursive", "--", "python", "main.py"]
