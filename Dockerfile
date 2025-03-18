# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей в контейнер
COPY requirements.txt .
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в рабочую директорию контейнера
COPY . /app

# Команда для запуска основного Python-файла
CMD ["python", "Controller/MainController.py"]