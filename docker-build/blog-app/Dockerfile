FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY docker-build/blog-app/entrypoint.sh /etc/entrypoint.sh
# убираем \r на случай, если файл сохранён на Windows с CRLF
RUN sed -i 's/\r$//' /etc/entrypoint.sh && chmod +x /etc/entrypoint.sh

COPY blog-app ./

ENTRYPOINT ["/etc/entrypoint.sh"]