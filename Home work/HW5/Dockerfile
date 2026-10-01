

#базовый образ
FROM python:3.12-slim

#рабочая директория внутри контейнера
WORKDIR /app

#копирование файлов в контейнер
COPY requirements.txt .

#использование pip для установки зависимостей
RUN pip install --no-cache-dir -r requirements.txt

#копирование файлов проекта в контейнер
COPY . .

#декларируем порты
EXPOSE 8000

#запуск приложения
CMD ["python", "app.py"]