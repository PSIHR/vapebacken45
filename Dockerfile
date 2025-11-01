# Используе официальный образ Python
FROM python:3.11-slim

# Не буферизовать вывод Python (полезно для логов)
ENV PYTHONUNBUFFERED=1

# Установить рабочую директорию внутри контейнера
WORKDIR /app

# Скопировать файл зависимостей и установить их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопировать всё содержимое проекта
COPY . .

# Открыть порт, на котором будет работать FastAPI
EXPOSE 8000

# Запустить приложение через Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "./certs/key.pem", "--ssl-certfile", "./certs/cert.pem"]

