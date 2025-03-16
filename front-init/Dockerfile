# Використовуємо офіційний образ Python
FROM python:3.12-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо всі файли проєкту
COPY . /app

# Встановлюємо необхідні пакети
RUN pip install --no-cache-dir -r requirements.txt

# Відкриваємо порти для HTTP та Socket-сервера
EXPOSE 3000
EXPOSE 5000

# Запускаємо головний файл
CMD ["python", "main.py"]
