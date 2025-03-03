import time
import requests
import random
import string
import re
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
import uvicorn
from telegram import Update, Chat
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")
ALLOWED_GROUP_ID = int(os.getenv("ALLOWED_GROUP_ID", -1002378339182))  # Replace with your group ID

REPORT_ENDPOINT = "https://groupsor.link/data/addreport"
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

app = FastAPI()

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

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Webhook handler for Telegram."""
    data = await request.json()
    update = Update.de_json(data, None)
    
    # Handling message updates
    if update.message and update.message.text:
        chat_id = update.message.chat_id
        text = update.message.text

        if chat_id == ALLOWED_GROUP_ID:
            urls = re.findall(r'https?://[^\s]+', text)
            if urls:
                for url in urls:
                    report_status = scrape_and_report(url)
                    await update.message.reply_text(report_status)

    return {"status": "ok"}

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

    if chat_id != ALLOWED_GROUP_ID:
        return

    text = update.message.text
    urls = re.findall(r'https?://[^\s]+', text)
    
    if urls:
        for url in urls:
            report_status = scrape_and_report(url)
            await update.message.reply_text(report_status)

def main():
    """Initializes the Telegram bot and the FastAPI app."""
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_group_messages))

    app.run_webhook()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
