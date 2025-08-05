FROM python:3.10-slim

# 1) System deps: Chrome, Tesseract, fonts, libs
RUN apt-get update && apt-get install -y \
    wget unzip gnupg2 tesseract-ocr \
    fonts-liberation libgtk-3-0 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 libxss1 libxtst6 libnss3 libasound2 libxfixes3 libxrender1 xdg-utils \
  && rm -rf /var/lib/apt/lists/*

# 2) Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update && apt-get install -y google-chrome-stable \
 && rm -rf /var/lib/apt/lists/*

# 3) Install matching Chromedriver (use POSIX grep)
RUN CHROME_VER=$(google-chrome --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+') \
 && DRIVER_VER=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VER%.*}) \
 && wget -O /tmp/chromedriver.zip \
      https://chromedriver.storage.googleapis.com/${DRIVER_VER}/chromedriver_linux64.zip \
 && unzip /tmp/chromedriver.zip -d /usr/bin/ \
 && chmod +x /usr/bin/chromedriver \
 && rm /tmp/chromedriver.zip

# 4) App setup
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# 5) Env vars for Python code
ENV CHROME_BINARY=/usr/bin/google-chrome-stable \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 6) Point WORKDIR to Django project
WORKDIR /app/sampada_scraper

EXPOSE 8000
CMD ["gunicorn", "sampada_scraper.wsgi:application", "--bind", "0.0.0.0:8000"]
