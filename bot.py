import os
import asyncio
import feedparser
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands, tasks
from datetime import datetime

# Web server pro Render Free tier
app = Flask('')

@app.route('/')
def home():
    return "Bot je naživu a hlídá daně!"

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

LAST_ARTICLE_LINK = None

# Seznam daňových termínů
DANE_TERMINY = [
    {"den": 20, "popis": "Měsíční přiznání a daň z přidané hodnoty (DPH)"},
    {"den": 25, "popis": "Kontrolní hlášení a souhrnné hlášení DPH"},
    {"den": 31, "popis": "Daň z nemovitých věcí / Daň z příjmů (dle období)"}
]

async def check_rss():
    global LAST_ARTICLE_LINK
    channel_id = os.getenv("CHANNEL_ID")
    if not channel_id:
        return
    channel = bot.get_channel(int(channel_id))
    if not channel:
        return

    feed = feedparser.parse("https://www.podnikatel.cz/rss/clanky/")
    if feed.entries:
        latest = feed.entries[0]
        if LAST_ARTICLE_LINK is None:
            LAST_ARTICLE_LINK = latest.link
        elif latest.link != LAST_ARTICLE_LINK:
            LAST_ARTICLE_LINK = latest.link
            embed = discord.Embed(
                title=f"📰 Nový článek: {latest.title}",
                url=latest.link,
                description=latest.get("summary", "Bez popisu"),
                color=0x3498db
            )
            embed.set_footer(text="Zdroj: Podnikatel.cz")
            await channel.send(embed=embed)

@tasks.loop(minutes=30)
async def rss_loop():
    await check_rss()

@tasks.loop(hours=24)
async def daily_check():
    channel_id = os.getenv("CHANNEL_ID")
    if not channel_id:
        return
    channel = bot.get_channel(int(channel_id))
    if not channel:
        return

    today = datetime.now()
    dny_v_mesici = [t for t in DANE_TERMINY if t["den"] >= today.day]
    
    if dny_v_mesici:
        msg = f"📅 **Daňový přehled pro tento měsíc ({today.strftime('%m/%Y')}):**\n"
        for term in dny_v_mesici:
            msg += f"• **{term['den']}. v měsíci**: {term['popis']}\n"
        await channel.send(msg)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} je připojen a spouští automatické hlídání!')
    if not rss_loop.is_running():
        rss_loop.start()
    if not daily_check.is_running():
        daily_check.start()

@bot.command(name="dane")
async def dane(ctx):
    today = datetime.now()
    msg = f"🔍 **Ruční kontrola daňových termínů ({today.strftime('%d.%m.%Y')}):**\n"
    for term in DANE_TERMINY:
        msg += f"• **{term['den']}. v měsíci**: {term['popis']}\n"
    await ctx.send(msg)
    await check_rss()

if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("Chybí DISCORD_TOKEN v proměnných prostředí!")
