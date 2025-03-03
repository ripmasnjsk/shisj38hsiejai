import time
import requests
import random
import string
import re
import asyncio
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# 🔹 Telegram bot token (Replace with yours)
BOT_TOKEN = "8161659596:AAHUtmeKjVS6_A2c7-oVReZccZ485JYp3mk"

# 🔹 Group chat ID where the bot should work (Replace with actual group ID)
ALLOWED_GROUP_ID = -1002378339182  # Replace with your group ID

# 🔹 Reporting endpoint
REPORT_ENDPOINT = "https://groupsor.link/data/addreport"

# 🔹 Fake user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

# ✅ Generate a random IP
def generate_random_ip():
    return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))

# ✅ Generate a random reason
def generate_random_reason():
    return random.choice(["Group is Full", "Link Revoked"])

# ✅ Generate a random description
def generate_random_rdesc():
    return ' '.join(''.join(random.choices(string.ascii_letters, k=random.randint(1, 3))) for _ in range(random.randint(1, 3)))

# ✅ Fetch the HTML content of a URL
def fetch_url(client, url, headers):
    try:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")
    return None

# ✅ Scrape and report the group
def scrape_and_report(url):
    try:
        with requests.Session() as client:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
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

                print(f"🚀 Reporting {url} with IP: {random_ip}")

                response = client.post(REPORT_ENDPOINT, data=payload, headers=headers)
                if response.status_code == 200:
                    return f"✅ Report submitted successfully for {url}"
                else:
                    return f"❌ Failed to submit report for {url}. Status: {response.status_code}"
            else:
                return f"❌ Could not fetch the page for {url}"
    
    except Exception as e:
        return f"❌ Error processing {url}: {e}"

# ✅ Start command handler
async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id == ALLOWED_GROUP_ID:
        await update.message.reply_text("👋 Hello! Send a group invite link in this chat, and I will report it.")
    else:
        await update.message.reply_text("❌ This bot only works in the specified group.")

# ✅ Help command handler
async def help_command(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id == ALLOWED_GROUP_ID:
        await update.message.reply_text("📌 Send any group invite link here, and I will report it.")
    else:
        await update.message.reply_text("❌ This bot only works in the designated group.")

# ✅ Process messages in the allowed group
async def handle_group_messages(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    # Ensure the bot only works in the allowed group
    if chat_id != ALLOWED_GROUP_ID:
        return  

    text = update.message.text

    # Extract URLs from the message
    urls = re.findall(r'https?://[^\s]+', text)
    
    if urls:
        for url in urls:
            report_status = scrape_and_report(url)
            await update.message.reply_text(report_status)

# ✅ Main function to run the bot properly
async def main():
    """Runs the Telegram bot with asyncio support."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Message Handler for Group Chat
    app.add_handler(MessageHandler(filters.TEXT, handle_group_messages))

    print("🚀 Bot is running and restricted to the specified group...")

    await app.run_polling()

# ✅ Run the bot properly in an async-safe way
if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(main())  # If event loop is already running, use create_task
    except RuntimeError:
        asyncio.run(main())  # If no event loop is running, start normally
