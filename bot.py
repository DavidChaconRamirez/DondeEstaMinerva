import discord
from discord.ext import commands
import os

# Define los intents que quieres utilizar
intents = discord.Intents.default()
intents.messages = True  # Permite recibir eventos de mensajes

# Obtiene el token y el ID del canal desde las variables de entorno
TOKEN = os.environ.get('DISCORD_TOKEN')  # Reemplaza 'DISCORD_TOKEN' con el nombre de la variable de entorno que configures en Railway
CHANNEL_ID = int(os.environ.get('DISCORD_CHANNEL_ID'))  # Reemplaza 'DISCORD_CHANNEL_ID' con el nombre de la variable de entorno que configures en Railway

# Configura el prefijo de comandos y los intents
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} ha iniciado sesión en Discord!')
    channel = bot.get_channel(CHANNEL_ID)
    if channel is not None:
        await channel.send('Hello World')  # Envía el mensaje "Hello World"
    else:
        print("El canal no fue encontrado. Verifica que el ID del canal sea correcto.")

@bot.event
async def on_message(message):
    # Evita que el bot responda a sus propios mensajes
    if message.author == bot.user:
        return

    # Si quieres agregar más lógica de mensajes, puedes hacerlo aquí
    await bot.process_commands(message)

# Inicia el bot
bot.run(TOKEN)
