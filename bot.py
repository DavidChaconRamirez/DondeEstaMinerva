import os
import time
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

# Configura el bot de Discord
TOKEN = os.getenv('DISCORD_TOKEN')  # Usar variable de entorno
ROLE_ID = os.getenv('ROLE_ID')
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True  # Necesario para escuchar eventos de guilds
bot = commands.Bot(command_prefix='!', intents=intents)

# Almacenar el ID del canal
channel_id = None

@bot.command(name='elige')
@commands.has_permissions(administrator=True)
async def choose_channel(ctx, channel: discord.TextChannel):
    global channel_id
    channel_id = channel.id
    await ctx.send(f"Canal elegido: {channel.mention}")

@choose_channel.error
async def choose_channel_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("Por favor, proporciona un canal válido.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("No tienes permisos para usar este comando.")
    else:
        await ctx.send(f"Ocurrió un error: {str(error)}")

async def send_to_discord(location, time_left, image_url, items):
    await bot.wait_until_ready()  # Esperar hasta que el bot esté listo

    if channel_id is None:
        # Enviar un mensaje al canal por defecto si no se ha elegido
        default_channel = bot.get_channel(channel_id)
        if default_channel:
            await default_channel.send("El canal no ha sido elegido. Usa !elige <canal> para seleccionar uno.")
        return  # Salir si el canal no está configurado

    channel = bot.get_channel(channel_id)
    if channel is None:
        await bot.get_channel(channel_id).send(f"El canal con ID {channel_id} no se encontró.")
        return  # Salir si el canal no existe

    sent_messages = []
    translator = Translator()
    translated_location = translator.translate(location, src='en', dest='es')

    # Procesa la ubicación traducida
    location_part = translated_location.text.split("en ", 1)[0].strip()
    
    place = location.split(" at ")[-1].strip() if " at " in location else ""

    # Si el lugar contiene un " in" al final, lo eliminamos
    if place.endswith(" in"):
        place = place[:-3].strip()

    # Si el lugar contiene un " for" al final, lo eliminamos
    if place.endswith(" for"):
        place = place[:-3].strip()

    if location_part.startswith("Ella"):
        location_part = location_part.replace("Ella", "").strip()

    final_message = f"¡Hola! <@&{ROLE_ID}> {location_part} en {place}"
    location_message = await channel.send(final_message)
    sent_messages.append(location_message)

    # Envía el tiempo restante
    hours, remainder = divmod(time_left, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_string = f"{hours:02}:{minutes:02}:{seconds:02}"
    countdown_message = await channel.send(f"**Tiempo restante:** {time_string}")
    sent_messages.append(countdown_message)

    # Manejo de la imagen
    if image_url.startswith('data:image/png;base64,'):
        image_data = image_url.split(',')[1]
        with open("image.png", "wb") as fh:
            fh.write(base64.b64decode(image_data))

        with open("image.png", "rb") as f:
            picture = discord.File(f)
            image_message = await channel.send(file=picture)
            sent_messages.append(image_message)

    # Envía los artículos del inventario
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
    # Calculamos el tiempo de finalización
    end_time = time.time() + time_left

    while time_left > 0:
        # Calcular el tiempo restante de manera precisa
        current_time = time.time()
        time_left = max(0, end_time - current_time)

        # Calcular días, horas, minutos y segundos restantes
        days, remainder = divmod(time_left, 86400)  # 86400 segundos en un día
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Formatear el tiempo
        time_string = f"{int(days):02}d {int(hours):02}h {int(minutes):02}m {int(seconds):02}s"
        
        # Actualizar el mensaje de tiempo restante
        await countdown_message.edit(content=f"**Tiempo restante:** {time_string}**")
        
        # Esperar 1 segundo antes de actualizar nuevamente
        await asyncio.sleep(0.7)

    # Eliminar todos los mensajes enviados cuando termine el conteo
    for message in sent_messages:
        await message.delete()

    # Reiniciar el proceso
    await on_ready()

def scrape_minerva():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        url = "https://www.whereisminerva.com"
        driver.get(url)

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
        if driver:
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
    print(f'{bot.user} ha iniciado sesión en Discord!')
    location, time_left, image_url, items = scrape_minerva()
    await send_to_discord(location, time_left, image_url, items)

bot.run(TOKEN)
