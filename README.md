# ДЗ №7: Взаимодействие между контейнерами

Flask + SQLAlchemy + Alembic + PostgreSQL, запуск через gunicorn за nginx.

## Запуск

    cp .env.example .env
    docker compose up -d --build

Приложение: http://localhost:8080

- `/posts/` — список постов, `/posts/add/` — новый пост
- `/users/` — список пользователей, `/users/add/` — новый пользователь

Миграции применяются автоматически при старте контейнера (`docker-build/blog-app/entrypoint.sh`).