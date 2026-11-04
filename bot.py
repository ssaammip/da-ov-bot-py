import os
import threading
from flask import Flask

# Miniaturní web server pro uspokojení Render Web Service
app = Flask('')

@app.route('/')
def home():
    return "Daňový hlídač běží 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Spuštění serveru na pozadí v samostatném vlákně
threading.Thread(target=run_flask, daemon=True).start()

# -----------------------------------------------------------------------------
# ZDE NÁSLEDUJE VÁŠ STÁVAJÍCÍ KÓD BOTA (import discord, intents, příkazy...)
# -----------------------------------------------------------------------------import os
import discord
from discord.ext import commands, tasks
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 📌 Názvy rolí na vašem Discordu pro označování
ROLE_PAUSAL = "osvc-pausalni dan"
ROLE_OSVC = "osvc"
ROLE_SRO = "majitel s.r.o."
ROLE_ZACATOCNIK = "začínající podnikatel"
ROLE_CLEN = "clen"

# 📅 DATABÁZE TERMÍNŮ S PŘIŘAZENÝMI ROLEMI
TERMINY_DATABAZE = [
    # Leden
    {"datum": "10.01. / 12.01.", "popis": "Lhůta pro přihlášení nebo odhlášení z paušální daně", "role": [ROLE_PAUSAL, ROLE_OSVC]},
    {"datum": "20.01.", "popis": "Měsíční splatnost zálohy na paušální daň / odvody zaměstnavatelů", "role": [ROLE_PAUSAL, ROLE_SRO]},
    {"datum": "25.01.", "popis": "DPH, KH a SH za měsíc prosinec a 4. čtvrtletí / Spotřební a energetické daně", "role": [ROLE_OSVC, ROLE_SRO]},
    {"datum": "31.01.", "popis": "Daňové přiznání k dani z nemovitých věcí & Přiznání k Silniční dani", "role": [ROLE_CLEN]},
    {"datum": "31.01.", "popis": "DPH v režimu OSS za 4. Q & Oznámení obratů přeshraničního DPH (SME)", "role": [ROLE_OSVC, ROLE_SRO]},
    
    # Únor
    {"datum": "15.02.", "popis": "Podpis Prohlášení poplatníka (růžový papír) a žádost o roční zúčtování", "role": [ROLE_SRO, ROLE_ZACATOCNIK]},
    {"datum": "20.02.", "popis": "Odvod záloh na daň z příjmů a pojištění za zaměstnance", "role": [ROLE_SRO]},
    
    # Březen
    {"datum": "01.03. / 20.03.", "popis": "Podání Vyúčtování daně ze závislé činnosti (papírově / elektronicky)", "role": [ROLE_SRO]},
    {"datum": "15.03.", "popis": "1. čtvrtletní záloha na daň z příjmů (při dani nad 150 tis. Kč)", "role": [ROLE_OSVC, ROLE_SRO]},
    {"datum": "31.03. / 01.04.", "popis": "Termín pro PAPÍROVÉ podání přiznání k dani z příjmů (FO i PO)", "role": [ROLE_OSVC, ROLE_SRO]},
    
    # Duben
    {"datum": "25.04.", "popis": "DPH, Kontrolní a Souhrnné hlášení za 1. čtvrtletí", "role": [ROLE_OSVC, ROLE_SRO]},
    {"datum": "30.04.", "popis": "Vyúčtování srážkové daně & Čtvrtletní pojištění odpovědnosti zaměstnavatele", "role": [ROLE_SRO]},
    {"datum": "30.04.", "popis": "DPH v režimu OSS za 1. Q & Výkazy pro ČSÚ (statistika)", "role": [ROLE_OSVC, ROLE_SRO]},
    
    # Květen
    {"datum": "02.05. / 04.05.", "popis": "Hlavní termín pro ELEKTRONICKÉ podání přiznání k dani z příjmů", "role": [ROLE_OSVC, ROLE_SRO, ROLE_ZACATOCNIK]},
    {"datum": "31.05.", "popis": "1. splátka daně z nemovitých věcí (při částce nad 5 000 Kč)", "role": [ROLE_CLEN]},
    
    # Červen
    {"datum": "15.06.", "popis": "Pololetní / 2. čtvrtletní záloha na daň z příjmů", "role": [ROLE_OSVC, ROLE_SRO]},
    {"datum": "30.06.", "popis": "Termín pro uplatnění vrácení spotřební daně (Zelená nafta)", "role": [ROLE_OSVC, ROLE_SRO]},
    {"datum": "30.06.", "popis": "Řádná valná hromada s.r.o. ke schválení účetní závěrky za minulý rok", "role": [ROLE_SRO]},
    
    # Červenec
    {"datum": "01.07.", "popis": "Podání daňového přiznání přes daňového poradce", "role": [ROLE_OSVC, ROLE_SRO]},
    {"datum": "25.07.", "popis": "DPH, Kontrolní a Souhrnné hlášení za 2. čtvrtletí", "role": [ROLE_OSVC, ROLE_SRO]},
    {"datum": "31.07.", "popis": "DPH v režimu OSS za 2. Q & Čtvrtletní pojištění odpovědnosti zaměstnavatele", "role": [ROLE_SRO]},
    
    # Září
    {"datum": "15.09.", "popis": "3. čtvrtletní záloha na daň z příjmů", "role": [ROLE_OSVC, ROLE_SRO]},
    
    # Říjen
    {"datum": "25.10.", "popis": "DPH, Kontrolní a Souhrnné hlášení za 3. čtvrtletí", "role": [ROLE_OSVC, ROLE_SRO]},
    {"datum": "31.10.", "popis": "DPH v režimu OSS za 3. Q & Čtvrtletní pojištění odpovědnosti zaměstnavatele", "role": [ROLE_SRO]},
    
    # Listopad
    {"datum": "30.11.", "popis": "2. splátka daně z nemovitých věcí & Přiznání k Windfall Tax", "role": [ROLE_CLEN, ROLE_SRO]},
    
    # Prosinec
    {"datum": "15.12.", "popis": "Pololetní / 4. čtvrtletní záloha na daň z příjmů", "role": [ROLE_OSVC, ROLE_SRO]},
    {"datum": "31.12.", "popis": "Povinnost zveřejnit účetní závěrku ve Sbírce listin Obchodního rejstříku", "role": [ROLE_SRO]}
]

# 📜 SCHVÁLENÉ ZMĚNY LEGISLATIVY ZA POSLEDNÍCH 6 MĚSÍCŮ
LEGISLATIVNI_ZMENY = [
    {"datum": "01.01.2026", "nazev": "Paušální daň 2026 (1. pásmo)", "popis": "Měsíční platba v 1. pásmu paušální daně činí přesně 9 984 Kč/měsíc."},
    {"datum": "01.01.2026", "nazev": "Sazba DPPO 21 %", "popis": "Sazba daně z příjmů právnických osob (s.r.o.) je potvrzena na výši 21 %."},
    {"datum": "01.01.2026", "nazev": "Vyměřovací základy OSVČ", "popis": "Vyměřovací základ pro sociální pojištění OSVČ činí 55 % a pro zdravotní pojištění 50 %."},
    {"datum": "01.11.2025", "nazev": "Kontrolní hlášení – Lhůta na výzvy", "popis": "Lhůta pro odpověď na výzvu z KH doručenou do datové schránky je striktně 17 dnů."}
]

def formatuj_role(role_list, guild):
    """Převede názvy rolí na označení (mentions) přímo na Discordu."""
    mentions = []
    for r_name in role_list:
        role = discord.utils.get(guild.roles, name=r_name)
        if role:
            mentions.append(role.mention)
        else:
            mentions.append(f"`@{r_name}`")
    return " ".join(mentions)

@bot.event
async def on_ready():
    print(f"✅ Daňový hlídač je spuštěn jako {bot.user}")
    pondelni_hlaseni.start()

# -----------------------------------------------------------------------------
# ⏰ AUTOMATICKÉ PONDĚLNÍ HLÁŠENÍ (Proběhne každé pondělí)
# -----------------------------------------------------------------------------
@tasks.loop(hours=168)
async def pondelni_hlaseni():
    # ⚠️ Nahraďte číslo níže vaším ID kanálu z KROKU 1
    KANAL_ID = 1567346984174489732  
    kanal = bot.get_channel(KANAL_ID)
    if not kanal:
        return

    embed = discord.Embed(
        title="📅 Pravidelný pondělní přehled daňových termínů",
        description="Zkontrolujte si nadcházející povinnosti podle vaší role na serveru:",
        color=0x3498DB
    )

    # Vypíše prvních 5 nejbližších termínů
    for t in TERMINY_DATABAZE[:5]:
        role_tags = formatuj_role(t["role"], kanal.guild)
        embed.add_field(
            name=f"📌 {t['datum']} – {t['popis']}",
            value=f"Pro role: {role_tags}",
            inline=False
        )

    embed.set_footer(text="Daňový Hlídač • Nezapomeňte na termíny včas!")
    await kanal.send(embed=embed)

# -----------------------------------------------------------------------------
# 🤖 DISCORD PŘÍKAZY
# -----------------------------------------------------------------------------

# 1. Příkaz pro výpis všech termínů
@bot.command(name="terminy")
async def prikaz_terminy(ctx):
    embed = discord.Embed(
        title="📅 Kompletní přehled daňových termínů",
        description="Seznam všech povinností a přiřazených rolí:",
        color=0x2ECC71
    )
    for t in TERMINY_DATABAZE:
        role_tags = formatuj_role(t["role"], ctx.guild)
        embed.add_field(
            name=f"{t['datum']} – {t['popis']}",
            value=f"Týká se: {role_tags}",
            inline=False
        )
    await ctx.send(embed=embed)

# 2. Příkaz pro výpis legislativních změn za 6 měsíců
@bot.command(name="legislativa")
async def prikaz_legislativa(ctx):
    embed = discord.Embed(
        title="⚖️ Přehled legislativních změn za posledních 6 měsíců",
        description="Důležité novely, změny sazeb a předpisů:",
        color=0xE74C3C
    )
    for z in LEGISLATIVNI_ZMENY:
        embed.add_field(
            name=f"🗓️ {z['datum']} – {z['nazev']}",
            value=f"{z['popis']}",
            inline=False
        )
    embed.set_footer(text="Daňový Hlídač 2026")
    await ctx.send(embed=embed)

# 3. Příkaz nápovědy
@bot.command(name="pomoc")
async def prikaz_pomoc(ctx):
    embed = discord.Embed(
        title="🤖 Příkazy Daňového hlídače",
        color=0xF1C40F
    )
    embed.add_field(name="`!terminy`", value="Zobrazí kompletní kalendář daňových termínů s označenými rolemi.", inline=False)
    embed.add_field(name="`!legislativa`", value="Zobrazí přehled změněné legislativy za posledních 6 měsíců.", inline=False)
    embed.add_field(name="`!pomoc`", value="Zobrazí tento přehled příkazů.", inline=False)
    await ctx.send(embed=embed)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
