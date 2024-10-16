import os
import asyncio
import base64
from discord.ext import commands
from playwright.async_api import async_playwright
import discord

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

# Configuración del bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Envío a Discord
async def send_to_discord(location, time_left, image_url, items):
    channel = bot.get_channel(int(CHANNEL_ID))
    sent_messages = []

    final_message = f"¡Hola! @Minerva {location}"
    location_message = await channel.send(final_message)
    sent_messages.append(location_message)

    hours, remainder = divmod(time_left, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_string = f"{hours:02}:{minutes:02}:{seconds:02}"
    countdown_message = await channel.send(f"**Tiempo restante:** {time_string}")
    sent_messages.append(countdown_message)

    # Enviar imagen si existe
    if image_url.startswith('data:image/png;base64,'):
        image_data = image_url.split(',')[1]
        with open("image.png", "wb") as fh:
            fh.write(base64.b64decode(image_data))

        with open("image.png", "rb") as f:
            picture = discord.File(f)
            image_message = await channel.send(file=picture)
            sent_messages.append(image_message)

    # Enviar lista de items
    grid_message = "**y nos trae esto:**\n"
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

# Contador de tiempo restante
async def countdown(channel, time_left, countdown_message, sent_messages):
    while time_left > 0:
        hours, remainder = divmod(time_left, 3600)
        minutes, seconds = divmod(remainder, 60)

        time_string = f"{hours:02}h {minutes:02}m {seconds:02}s"
        await countdown_message.edit(content=f"**Tiempo restante:** {time_string}")
        await asyncio.sleep(1)
        time_left -= 1

    for message in sent_messages:
        await message.delete()

# Scraping con Playwright
async def scrape_minerva():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.whereisminerva.com")
        await page.wait_for_timeout(5000)

        location = await page.locator(".location-header").inner_text()
        time_left_str = await page.locator(".time-display").inner_text()
        time_left = convert_time_to_seconds(time_left_str)
        image_url = await page.locator(".location-image img").get_attribute('src')

        inventory_items = []
        items = await page.locator(".itemcard").all()
        for item in items:
            item_name = await item.locator(".itemname").inner_text()
            item_price = await item.locator(".bullion").inner_text()
            inventory_items.append({'name': item_name, 'price': item_price.strip()})

        await browser.close()
        return location, time_left, image_url, inventory_items

# Conversión de tiempo
def convert_time_to_seconds(time_str):
    days = hours = minutes = seconds = 0
    time_parts = time_str.split()
    for part in time_parts:
        if 'd' in part:
            days = int(part.replace('d', ''))
        elif 'h' in part:
            hours = int(part.replace('h', ''))
        elif 'm' in part:
            minutes = int(part.replace('m', ''))
        elif 's' in part:
            seconds = int(part.replace('s', ''))

    return (days * 86400) + (hours * 3600) + (minutes * 60) + seconds

# Evento de inicio
@bot.event
async def on_ready():
    location, time_left, image_url, items = await scrape_minerva()
    await send_to_discord(location, time_left, image_url, items)

bot.run(TOKEN)
