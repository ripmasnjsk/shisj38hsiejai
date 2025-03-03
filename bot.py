import requests
import random
import string
import re
from bs4 import BeautifulSoup
from flask import Flask, request
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ALLOWED_GROUP_ID = int(os.getenv("ALLOWED_GROUP_ID", -1002378339182))  # Replace with your group ID
REPORT_ENDPOINT = "https://groupsor.link/data/addreport"
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

# Flask app setup for webhook or any additional use
app = Flask(__name__)

def generate_random_ip():
    return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))

def generate_random_reason():
    return random.choice(["Group is Full", "Link Revoked"])

def generate_random_rdesc():
    return ' '.join(''.join(random.choices(string.ascii_letters, k=random.randint(1, 3))) for _ in range(random.randint(1, 3)))

def fetch_url(client, url, headers):
    try:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
    return None

def scrape_and_report(url):
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

# Define the /start command handler
async def start(update: Update, context):
    """Handles the /start command."""
    await update.message.reply_text("Welcome to the reporting bot. Send a group invite link to report.")

# Define the /help command handler
async def help_command(update: Update, context):
    """Handles the /help command."""
    await update.message.reply_text("Send any group invite link in this chat to report it.")

# Define the message handler for group messages
async def handle_group_messages(update: Update, context):
    """Handles messages in the allowed group chat."""
    chat_id = update.message.chat_id

    if chat_id != ALLOWED_GROUP_ID:
        return  # Ignore messages from other groups

    text = update.message.text

    # Extract URLs from the message
    urls = re.findall(r'https?://[^\s]+', text)
    
    if urls:
        for url in urls:
            report_status = scrape_and_report(url)
            await update.message.reply_text(report_status)

# Telegram bot main function
def main():
    """Initialize the Telegram bot."""
    bot_app = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_group_messages))

    bot_app.run_polling()

if __name__ == "__main__":
    main()
