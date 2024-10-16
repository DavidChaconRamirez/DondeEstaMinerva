# Usamos una imagen base de Python
FROM python:3.11-slim

# Actualizamos el sistema e instalamos las dependencias necesarias
RUN apt-get update && apt-get install -y \
    wget \
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
    fonts-liberation

# Instalar Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
dpkg -i google-chrome-stable_current_amd64.deb || apt-get -fy install && \
rm google-chrome-stable_current_amd64.deb

# Instalar ChromeDriver
RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
wget -N http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip -P /tmp && \
unzip /tmp/chromedriver_linux64.zip -d /opt/chromedriver && \
rm /tmp/chromedriver_linux64.zip && \
ln -s /opt/chromedriver/chromedriver /usr/local/bin/chromedriver

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de tu bot al contenedor
COPY . /app

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar el bot
CMD ["python", "bot.py"]
