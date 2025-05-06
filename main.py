import discord
from discord import app_commands
from discord.ext import commands
import os
import pytesseract
import cv2
import json
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from rapidfuzz import fuzz
from typing import List
from dotenv import load_dotenv
import platform

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SERVER_ID = os.getenv("SERVER_ID")
ADMIN_ROLE_ID = os.getenv("ADMIN_ROLE_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Tesseract path (adjust if needed)
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

GUILD_FILE = "guild_members.json"
ATTENDANCE_FILE = "attendance_count.json"
ATTENDANCE_LOG_FILE = "attendance_log.json"
last_attendance = []

# --- Helper functions ---

def save_guild_members(members):
    with open(GUILD_FILE, "w", encoding="utf-8") as f:
        json.dump({"members": members}, f)

def load_guild_members():
    if not os.path.exists(GUILD_FILE):
        return []
    with open(GUILD_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("members", [])

def has_admin_role(interaction: discord.Interaction):
    return any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)

def load_attendance_counts():
    if not os.path.exists(ATTENDANCE_FILE):
        return {}
    with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_attendance_counts(counts):
    with open(ATTENDANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2)

def load_attendance_log():
    if not os.path.exists(ATTENDANCE_LOG_FILE):
        return {}
    with open(ATTENDANCE_LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_attendance_log(log):
    with open(ATTENDANCE_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

# --- Slash Commands ---

@bot.tree.command(name="today", description="See who joined CTA today", guild=discord.Object(id=SERVER_ID))
async def today(interaction: discord.Interaction):
    today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log = load_attendance_log()
    joined_today = log.get(today_key, [])

    if not joined_today:
        await interaction.response.send_message("📭 No one has joined any CTA yet today.")
        return

    joined_today.sort()
    formatted = "\n".join(f"{i+1}. {name}" for i, name in enumerate(joined_today))
    embed = discord.Embed(title=f"✅ Members in CTA today ({len(joined_today)})", description=formatted, color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="yesterday", description="See who joined CTA yesterday", guild=discord.Object(id=SERVER_ID))
async def yesterday(interaction: discord.Interaction):
    yesterday_key = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    log = load_attendance_log()
    joined_yesterday = log.get(yesterday_key, [])

    if not joined_yesterday:
        await interaction.response.send_message("📭 No one joined any CTA yesterday.")
        return

    joined_yesterday.sort()
    formatted = "\n".join(f"{i+1}. {name}" for i, name in enumerate(joined_yesterday))
    embed = discord.Embed(title=f"📆 Members in CTA yesterday ({len(joined_yesterday)})", description=formatted, color=discord.Color.orange())
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=SERVER_ID))
    print(f"✅ Bot is ready as {bot.user}")

@bot.tree.command(name="set", description="Upload .txt or .json with guild members", guild=discord.Object(id=SERVER_ID))
async def setmembers(interaction: discord.Interaction, file: discord.Attachment):
    if not has_admin_role(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    await interaction.response.defer()
    file_bytes = await file.read()

    if file.filename.endswith(".txt"):
        names = file_bytes.decode("utf-8").splitlines()
    elif file.filename.endswith(".json"):
        data = json.loads(file_bytes)
        names = data.get("members", [])
    else:
        await interaction.followup.send("❌ Please upload a `.txt` or `.json` file.")
        return

    save_guild_members([n.strip() for n in names if n.strip()])
    await interaction.followup.send(f"✅ Saved {len(names)} guild members.")

@bot.tree.command(name="list", description="Show current guild members", guild=discord.Object(id=SERVER_ID))
async def listmembers(interaction: discord.Interaction):
    members = load_guild_members()
    counts = load_attendance_counts()
    if not members:
        await interaction.response.send_message("⚠️ No members found.")
        return
    members.sort(key=lambda x: (-counts.get(x, 0), x.lower()))
    formatted = "\n".join(f"{i+1}. {m} ({counts.get(m, 0)})" for i, m in enumerate(members))
    embed = discord.Embed(title="📋 Guild Members", description=f"{formatted}", color=discord.Color.green())
    embed.set_footer(text=f"Total: {len(members)} members")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="filter", description="Show members filtered by attendance using operators", guild=discord.Object(id=SERVER_ID))
@app_commands.describe(operator="Comparison operator: =, <, <=, >, >=", value="Attendance count to compare against")
async def filtermembers(interaction: discord.Interaction, operator: str, value: int):
    members = load_guild_members()
    counts = load_attendance_counts()
    op_map = {
        "=": lambda x: x == value,
        "<": lambda x: x < value,
        "<=": lambda x: x <= value,
        ">": lambda x: x > value,
        ">=": lambda x: x >= value
    }
    if operator not in op_map:
        await interaction.response.send_message("❌ Invalid operator. Use one of: =, <, <=, >, >=")
        return

    check = op_map[operator]
    filtered = [m for m in members if check(counts.get(m, 0))]
    filtered.sort(key=lambda x: (-counts.get(x, 0), x.lower()))
    if not filtered:
        await interaction.response.send_message(f"✅ No members matched condition: attendance {operator} {value}.")
        return
    formatted = "\n".join(f"{i+1}. {m} ({counts.get(m, 0)})" for i, m in enumerate(filtered))
    embed = discord.Embed(title=f"🔍 Filtered Members (attendance {operator} {value})", description=formatted, color=discord.Color.orange())
    embed.set_footer(text=f"Total: {len(filtered)} members")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="add", description="Add a member", guild=discord.Object(id=SERVER_ID))
@app_commands.describe(name="The server nickname to add")
async def add(interaction: discord.Interaction, name: str):
    members = load_guild_members()
    # Case-insensitive duplicate check
    if any(m.lower() == name.lower() for m in members):
        await interaction.response.send_message("⚠️ Member already exists (case-insensitive match).")
        return
    members.append(name)
    save_guild_members(members)
    await interaction.response.send_message(f"✅ Added `{name}` to the guild.")

@bot.tree.command(name="remove", description="Remove a member", guild=discord.Object(id=SERVER_ID))
@app_commands.describe(name="The name to remove")
async def remove(interaction: discord.Interaction, name: str):
    if not has_admin_role(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    members = load_guild_members()
    updated = [m for m in members if m.lower() != name.lower()]
    if len(updated) == len(members):
        await interaction.response.send_message("❌ Member not found.")
        return
    save_guild_members(updated)
    await interaction.response.send_message(f"🗑️ Removed `{name}` from the guild.")

@bot.tree.command(name="clear", description="Clear all members", guild=discord.Object(id=SERVER_ID))
async def clear(interaction: discord.Interaction):
    if not has_admin_role(interaction):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    if os.path.exists(GUILD_FILE):
        os.remove(GUILD_FILE)
        await interaction.response.send_message("🗑️ Cleared all members.")
    else:
        await interaction.response.send_message("❌ No member list found.")

@bot.command(name="check")
async def check(ctx):
    global last_attendance
    last_attendance = []
    if not ctx.message.attachments:
        await ctx.send("📎 Please attach one or more party screenshots.")
        return

    members = load_guild_members()
    attendance_counts = load_attendance_counts()
    attendance_log = load_attendance_log()
    today_key = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d")

    if not members:
        await ctx.send("⚠️ No guild member list found. Use `/set` first.")
        return

    detected_names = set()

    for attachment in ctx.message.attachments:
        file_path = f"temp_{ctx.author.id}_{attachment.filename}"
        await attachment.save(file_path)

        img = cv2.imread(file_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, None, fx=2, fy=2)
        thresh = cv2.threshold(resized, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        text = pytesseract.image_to_string(thresh)
        os.remove(file_path)

        detected = [line.strip() for line in text.split("\n") if len(line.strip()) > 2]
        detected_names.update(detected)

    matched = []
    for d in detected_names:
        for m in members:
            if fuzz.ratio(d.lower(), m.lower()) >= 80:
                matched.append(m)
                attendance_counts[m] = attendance_counts.get(m, 0) + 1
                attendance_log.setdefault(today_key, [])
                if m not in attendance_log[today_key]:
                    attendance_log[today_key].append(m)
                break

    save_attendance_counts(attendance_counts)
    save_attendance_log(attendance_log)
    matched.sort(key=lambda x: (-attendance_counts.get(x, 0), x.lower()))
    last_attendance = matched
    absent_members = [m for m in members if m not in matched]
    absent_members.sort(key=lambda x: (-attendance_counts.get(x, 0), x.lower()))

    if matched:
        formatted = "\n".join(f"{i+1}. {m} ({attendance_counts.get(m, 0)})" for i, m in enumerate(matched))
        embed = discord.Embed(title="✅ Members in CTA", description=formatted, color=discord.Color.blue())
        embed.set_footer(text=f"Present: {len(matched)} | Absent: {len(absent_members)}")
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ No guild members detected.")

    if absent_members:
        absent_text = "\n".join(f"{i+1}. {m} ({attendance_counts.get(m, 0)})" for i, m in enumerate(absent_members))
        embed_absent = discord.Embed(title="❌ Absent Members", description=absent_text, color=discord.Color.red())
        await ctx.send(embed=embed_absent)

# --- Start the bot ---
bot.run(DISCORD_BOT_TOKEN)