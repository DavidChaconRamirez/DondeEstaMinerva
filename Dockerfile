# Usar una imagen base de Python
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgbm1 \
    libgtk-3-0 \
    libxss1 \
    libxtst6 \
    libappindicator3-1 \
    fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

# Descargar e instalar Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb || apt-get -fy install && \
    rm google-chrome-stable_current_amd64.deb

# Crear directorio para ChromeDriver
RUN mkdir -p /opt/chromedriver

# Descargar e instalar ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -N http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip -P /tmp && \
    unzip /tmp/chromedriver_linux64.zip -d /opt/chromedriver && \
    rm /tmp/chromedriver_linux64.zip && \
    ln -s /opt/chromedriver/chromedriver /usr/local/bin/chromedriver

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto
COPY . /app

# Instalar las dependencias del proyecto
RUN pip install -r requirements.txt

# Comando para ejecutar el bot de Discord
CMD ["python", "bot.py"]
