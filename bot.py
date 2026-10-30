import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands, tasks

# Web server pro Render Free tier
app = Flask('')

@app.route('/')
def home():
    return "Bot je naživu!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} je připojen a běží!')

@bot.command(name="dane")
async def dane(ctx):
    await ctx.send("Provádím ruční kontrolu termínů a novinek...")

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("Chybí DISCORD_TOKEN v proměnných prostředí!")
