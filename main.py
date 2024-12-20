import os
import time
import requests
import base64
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import discord
from discord.ext import commands
from googletrans import Translator
import re

# Configura el bot de Discord
TOKEN = os.getenv('DISCORD_TOKEN')  # Usar variable de entorno
CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')  # Usar variable de entorno
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def clear_channel_messages(channel):
    """Elimina todos los mensajes en un canal."""
    try:
        async for message in channel.history(limit=None):
            await message.delete()
        print(f"Mensajes eliminados del canal {channel.name}.")
    except Exception as e:
        print(f"Error al intentar eliminar los mensajes: {e}")

async def send_to_discord(location, time_left, image_url, items):
    channel = bot.get_channel(int(CHANNEL_ID))
    if channel is None:
        print(f"Error: No se pudo encontrar el canal con ID {CHANNEL_ID}.")
        return

    # Borra todos los mensajes en el canal antes de enviar nuevos
    print("Limpiando el canal...")
    await clear_channel_messages(channel)
    print("Canal limpio. Enviando nuevos mensajes...")

    sent_messages = []
    translator = Translator()
    translated_location = translator.translate(location, src='en', dest='es')

    split_text = translated_location.text.split("en ", 1)
    if len(split_text) > 1:
        location_part = split_text[0].strip()
        place = location.split(" at ")[-1].strip()
    else:
        location_part = translated_location.text
        place = ""

    if location_part.startswith("Ella"):
        location_part = location_part.replace("Ella", "").strip()

    if place.endswith(" in"):
        place = place[:-3].strip()

    final_message = f"¡Hola! @Minerva {location_part} en {place}"
    location_message = await channel.send(final_message)
    sent_messages.append(location_message)

    hours, remainder = divmod(time_left, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_string = f"{hours:02}:{minutes:02}:{seconds:02}"
    countdown_message = await channel.send(f"**Tiempo restante:** {time_string}")
    sent_messages.append(countdown_message)

    if image_url.startswith('data:image/png;base64,'):
        image_data = image_url.split(',')[1]
        with open("image.png", "wb") as fh:
            fh.write(base64.b64decode(image_data))

        with open("image.png", "rb") as f:
            picture = discord.File(f)
            image_message = await channel.send(file=picture)
            sent_messages.append(image_message)

    grid_message = f"**y nos trae esto:**\n"
    items_per_row = 3
    for index, item in enumerate(items):
        item_name = item['name']
        item_price = item['price']
        grid_message += f"**{item_name}** - Precio: {item_price} bullion\n"
        if (index + 1) % items_per_row == 0:
            grid_message_message = await channel.send(grid_message)
            sent_messages.append(grid_message_message)
            grid_message = ""

    if grid_message:
        remaining_message = await channel.send(grid_message)
        sent_messages.append(remaining_message)

    await countdown(channel, time_left, countdown_message, sent_messages)

async def countdown(channel, time_left, countdown_message, sent_messages):
    while time_left > 0:
        days, remainder = divmod(time_left, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        time_string = f"{days:02}d {hours:02}h {minutes:02}m {seconds:02}s"
        await countdown_message.edit(content=f"**Tiempo restante:** {time_string}")
        await asyncio.sleep(1)
        time_left -= 1

    for message in sent_messages:
        await message.delete()

def scrape_minerva():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    url = "https://www.whereisminerva.com"
    driver.get(url)

    try:
        wait = WebDriverWait(driver, 10)
        location = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".location-header"))).text
        time_left_str = driver.find_element(By.CSS_SELECTOR, ".time-display").text
        time_left = convert_time_to_seconds(time_left_str)
        image_url = driver.find_element(By.CSS_SELECTOR, ".location-image img").get_attribute('src')

        inventory_items = []
        items = driver.find_elements(By.CSS_SELECTOR, ".itemcard")
        for item in items:
            item_name = item.find_element(By.CSS_SELECTOR, ".itemname").text
            item_price = item.find_element(By.CSS_SELECTOR, ".bullion").text.strip()
            inventory_items.append({'name': item_name, 'price': item_price})

    except Exception as e:
        print(f"Error durante el scraping: {e}")
    finally:
        driver.quit()

    return location, time_left, image_url, inventory_items

def convert_time_to_seconds(time_str):
    days = hours = minutes = seconds = 0
    time_parts = time_str.split()
    for part in time_parts:
        if 'd' in part:
            days = int(part.replace('d', '').strip())
        elif 'h' in part:
            hours = int(part.replace('h', '').strip())
        elif 'm' in part:
            minutes = int(part.replace('m', '').strip())
        elif 's' in part:
            seconds = int(part.replace('s', '').strip())

    total_seconds = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds
    return total_seconds

@bot.event
async def on_ready():
    print(f"{bot.user.name} está listo y conectado.")
    
    # Obtén el canal por ID
    channel = bot.get_channel(int(CHANNEL_ID))
    
    # Realiza el scraping y envía los nuevos mensajes
    location, time_left, image_url, items = scrape_minerva()
    await send_to_discord(location, time_left, image_url, items)

bot.run(TOKEN)
