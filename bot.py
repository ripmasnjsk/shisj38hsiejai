import time
import requests
import random
import string
import re
from bs4 import BeautifulSoup
from telegram import Update, Chat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from flask import Flask
import os
import asyncio

# Telegram bot token (Get from BotFather)
BOT_TOKEN = "8161659596:AAHUtmeKjVS6_A2c7-oVReZccZ485JYp3mk"

# Group chat ID (replace with actual ID)
ALLOWED_GROUP_ID = -1002378339182  # Replace with your actual group ID

# Reporting endpoint
REPORT_ENDPOINT = "https://groupsor.link/data/addreport"

# List of fake user agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

def generate_random_ip():
    """Generates a fake IP address."""
    return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))

def generate_random_reason():
    """Generates a random report reason."""
    return random.choice(["Group is Full", "Link Revoked"])

def generate_random_rdesc():
    """Generates a short random description."""
    return ' '.join(''.join(random.choices(string.ascii_letters, k=random.randint(1, 3))) for _ in range(random.randint(1, 3)))

def fetch_url(client, url, headers):
    """Fetches the HTML content from a URL."""
    try:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
    return None

def scrape_and_report(url):
    """Scrapes the page and submits a report."""
    try:
        with requests.Session() as client:
            headers = {"User-Agent": random.choice(user_agents)}
            html_content = fetch_url(client, url, headers)

            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')

                gpid = soup.find('input', {'name': 'gpid'}).get('value')
                code = soup.find('input', {'name': 'code'}).get('value')
                key = soup.find('input', {'name': 'key'}).get('value')
                val1 = int(soup.find('input', {'name': 'val1'}).get('value'))
                val2 = int(soup.find('input', {'name': 'val2'}).get('value'))
                expected_result = val1 + val2

                payload = {
                    "gpid": gpid,
                    "code": code,
                    "key": key,
                    "reason": generate_random_reason(),
                    "rdesc": generate_random_rdesc(),
                    "val1": val1,
                    "val2": val2,
                    "val3": expected_result
                }

                random_ip = generate_random_ip()
                headers.update({
                    "X-Forwarded-For": random_ip,
                    "X-Real-IP": random_ip
                })

                print(f"Reporting {url} with IP: {random_ip}")

                response = client.post(REPORT_ENDPOINT, data=payload, headers=headers)
                if response.status_code == 200:
                    return f"✅ Report submitted successfully for {url}"
                else:
                    return f"❌ Failed to submit report for {url}. Status: {response.status_code}"
            else:
                return f"❌ Could not fetch the page for {url}"
    
    except Exception as e:
        return f"❌ Error processing {url}: {e}"

async def start(update: Update, context: CallbackContext):
    """Handles /start command - Only works in the allowed group."""
    chat_id = update.message.chat_id
    if chat_id == ALLOWED_GROUP_ID:
        await update.message.reply_text("Hello! Send any group invite link in this chat, and I will report it.")
    else:
        await update.message.reply_text("❌ This bot only works in the designated group.")

async def help_command(update: Update, context: CallbackContext):
    """Handles /help command - Only works in the allowed group."""
    chat_id = update.message.chat_id
    if chat_id == ALLOWED_GROUP_ID:
        await update.message.reply_text("📌 Send any group invite link in this chat, and I will report it.")
    else:
        await update.message.reply_text("❌ This bot only works in the designated group.")

async def handle_group_messages(update: Update, context: CallbackContext):
    """Processes messages in the allowed group chat and extracts URLs for reporting."""
    chat_id = update.message.chat_id

    # Only allow messages from the specific group
    if chat_id != ALLOWED_GROUP_ID:
        return  # Ignore messages from other groups

    text = update.message.text

    # Extract URLs from the message
    urls = re.findall(r'https?://[^\s]+', text)
    
    if urls:
        for url in urls:
            report_status = scrape_and_report(url)
            await update.message.reply_text(report_status)

app_flask = Flask(__name__)

@app_flask.route('/')
def index():
    return "Flask app is running!"

async def run_flask():
    """Runs the Flask app."""
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

async def main():
    """Runs the Telegram bot."""
    app_telegram = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("help", help_command))

    # Message Handler for Group Chat (Filters Links & Enforces Group Restriction)
    app_telegram.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_group_messages))

    print("Bot is running and restricted to the specified group...")

    await app_telegram.start()
    await app_telegram.updater.start_polling()
    await app_telegram.updater.idle()

async def run_both():
    """Runs both Flask and Telegram bot together."""
    await asyncio.gather(run_flask(), main())

if __name__ == "__main__":
    asyncio.run(run_both())
