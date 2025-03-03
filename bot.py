import time
import requests
import random
import string
import re
from bs4 import BeautifulSoup
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Flask app to keep Render service alive
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200  # Render needs a web server to keep running

# Telegram bot setup
BOT_TOKEN = "8161659596:AAHUtmeKjVS6_A2c7-oVReZccZ485JYp3mk"
ALLOWED_GROUP_ID = -1002378339182  # Replace with your actual group ID

REPORT_ENDPOINT = "https://groupsor.link/data/addreport"

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

def generate_random_ip():
    return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))

def generate_random_reason():
    return random.choice(["Group is Full", "Link Revoked"])

def generate_random_rdesc():
    return ' '.join(''.join(random.choices(string.ascii_letters, k=random.randint(1, 3))) for _ in range(random.randint(1, 3)))

def scrape_and_report(url):
    try:
        with requests.Session() as client:
            headers = {"User-Agent": random.choice(user_agents)}
            response = client.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

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

            response = client.post(REPORT_ENDPOINT, data=payload, headers=headers)
            if response.status_code == 200:
                return f"✅ Report submitted successfully for {url}"
            else:
                return f"❌ Failed to submit report for {url}. Status: {response.status_code}"

    except Exception as e:
        return f"❌ Error processing {url}: {e}"

async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id == ALLOWED_GROUP_ID:
        await update.message.reply_text("Hello! Send any group invite link in this chat, and I will report it.")
    else:
        await update.message.reply_text("❌ This bot only works in the designated group.")

async def handle_group_messages(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id != ALLOWED_GROUP_ID:
        return  

    text = update.message.text
    urls = re.findall(r'https?://[^\s]+', text)
    
    if urls:
        for url in urls:
            report_status = scrape_and_report(url)
            await update.message.reply_text(report_status)

def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_group_messages))

    print("Bot is running...")
    app.run_polling()

import threading
threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # Flask keeps Render service running
