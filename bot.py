import os
import datetime
import asyncio
import requests
import feedparser
import discord
from discord.ext import commands
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

scheduler = AsyncIOScheduler(timezone="Europe/Prague")

TAX_DEADLINES = [
    # Lednové termíny
    (1, 10, "Lhůta pro přihlášení do režimu paušální daně"),
    (1, 25, "DPH a Kontrolní hlášení za 4. čtvrtletí / prosinec"),
    (1, 31, "Termín pro podání daňového přiznání k dani z nemovitých věcí"),
    
    # Únorové termíny
    (2, 15, "Termín pro žádost zaměstnance o roční zúčtování daně"),
    (2, 25, "DPH a Kontrolní hlášení za leden"),
    
    # Březnové termíny
    (3, 15, "1. čtvrtletní záloha na daň z příjmů"),
    (3, 25, "DPH a Kontrolní hlášení za únor"),
    
    # Dubnové termíny
    (4, 1, "Termín pro papírové podání přiznání k dani z příjmů (DPFO/DPPO)"),
    (4, 25, "DPH a Kontrolní hlášení za 1. čtvrtletí / březen"),
    
    # Květnové termíny
    (5, 2, "Termín pro elektronické podání přiznání k dani z příjmů"),
    (5, 25, "DPH a Kontrolní hlášení za duben"),
    (5, 31, "Splatnost daně z nemovitých věcí (nebo 1. splátky)"),
    
    # Červnové termíny
    (6, 2, "Termín pro odevzdání Přehledů ČSSZ a ZP (při el. podání DP)"),
    (6, 15, "2. čtvrtletní / 1. pololetní záloha na daň z příjmů"),
    (6, 25, "DPH a Kontrolní hlášení za květen"),
    
    # Červencové termíny
    (7, 1, "Termín podání DPFO/DPPO s daňovým poradcem / auditem"),
    (7, 25, "DPH a Kontrolní hlášení za 2. čtvrtletí / červen"),
    
    # Podzimní a zimní termíny
    (9, 15, "3. čtvrtletní záloha na daň z příjmů"),
    (9, 25, "DPH a Kontrolní hlášení za srpen"),
    (10, 25, "DPH a Kontrolní hlášení za 3. čtvrtletí / září"),
    (12, 15, "4. čtvrtletní / 2. pololetní záloha na daň z příjmů"),
    (12, 25, "DPH a Kontrolní hlášení za listopad"),
]

seen_articles = set()

async def check_tax_news():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    rss_url = "https://www.podnikatel.cz/rss/rubriky/dane/"
    feed = feedparser.parse(rss_url)

    for entry in feed.entries[:5]:
        if entry.link not in seen_articles:
            seen_articles.add(entry.link)
            embed = discord.Embed(
                title="📰 Novinka v daňové legislativě",
                description=entry.title,
                url=entry.link,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Zdroj: Podnikatel.cz")
            await channel.send(embed=embed)

async def check_deadlines():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    today = datetime.date.today()

    for month, day, title in TAX_DEADLINES:
        try:
            deadline_date = datetime.date(today.year, month, day)
        except ValueError:
            continue

        days_left = (deadline_date - today).days

        if days_left == 14:
            embed = discord.Embed(
                title="⏳ Blíží se daňový termín (za 14 dní)",
                description=f"**{title}**\nDatum splatnosti/podání: **{deadline_date.strftime('%d.%m.%Y')}**",
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)

        elif days_left == 3:
            embed = discord.Embed(
                title="⚠️ POZOR: Daňový termín je za 3 dny!",
                description=f"**{title}**\nDatum splatnosti/podání: **{deadline_date.strftime('%d.%m.%Y')}**\nNezapomeňte připravit podklady nebo odeslat platbu.",
                color=discord.Color.orange()
            )
            await channel.send(embed=embed)

        elif days_left == 0:
            embed = discord.Embed(
                title="🚨 DNES JE MEZNÍ TERMÍN!",
                description=f"**{title}**\nDnes (**{deadline_date.strftime('%d.%m.%Y')}**) je poslední den pro splnění této povinnosti!",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} je úspěšně připojen a běží!')
    scheduler.add_job(check_tax_news, 'interval', hours=2)
    scheduler.add_job(check_deadlines, 'cron', hour=8, minute=0)
    scheduler.start()

@bot.command(name="dane")
async def manual_check(ctx):
    await ctx.send("Provádím ruční kontrolu termínů a novinek...")
    await check_deadlines()
    await check_tax_news()

bot.run(TOKEN)
