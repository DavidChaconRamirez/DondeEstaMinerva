# Usa una imagen base oficial de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libpangoft2-1.0-0 \
    libpangoxft-1.0-0 \
    xdg-utils \
    fonts-liberation \
    libappindicator3-1 \
    libcurl4 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Agregar el repositorio de Google Chrome y su clave GPG
RUN curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Instalar Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable

# Establecer el binario de Chrome
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_PATH=/usr/bin/google-chrome

# Instalar ChromeDriver (necesario para Selenium)
RUN wget -N https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && rm chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver

# Establecer el display en modo headless
ENV DISPLAY=:99

# Instalar Playwright y dependencias
RUN pip install --upgrade pip \
    && pip install playwright \
    && playwright install

# Copiar los archivos del bot al directorio de trabajo
COPY . /app

# Instalar las dependencias del bot
RUN pip install -r requirements.txt

# Ejecutar el bot
CMD ["python", "bot.py"]
