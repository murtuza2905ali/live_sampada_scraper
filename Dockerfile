FROM python:3.10-slim

# 1) System deps: Chromium, Tesseract, fonts, libs
RUN apt-get update && apt-get install -y \
    wget unzip gnupg2 tesseract-ocr \
    chromium chromium-driver \
    fonts-liberation libgtk-3-0 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 libxss1 libxtst6 libnss3 libasound2 libxfixes3 libxrender1 xdg-utils \
  && rm -rf /var/lib/apt/lists/*

# 2) App setup
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# 3) Env vars for Python code (pointing to Chromium)
ENV CHROME_BINARY=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromium-driver

# 4) Expose & run from /app (where manage.py lives)
EXPOSE 8000
CMD ["gunicorn", "sampada_scraper.wsgi:application", "--chdir", "/app", "--bind", "0.0.0.0:8000"]
