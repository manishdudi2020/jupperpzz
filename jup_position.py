import requests
import json
import telebot
from datetime import datetime

# 🚀 Telegram Bot Token
BOT_TOKEN = "8172006250:AAHganSICLUvoOscSbXZl35UsjRBOhY_cXU"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# 🌐 API Endpoint
PERPS_API_BASE = "https://perps-api.jup.ag/v1"

# 🔍 Function to fetch trades
def get_trades(wallet):
    url = f"{PERPS_API_BASE}/trades?walletAddress={wallet}"
    print(f"📡 Fetching trades from: {url}")
    response = requests.get(url)
    print(f"🔄 API Response Code: {response.status_code}")

    if response.status_code == 200:
        json_data = response.json()
        print(f"✅ Response Data:\n{json.dumps(json_data, indent=4)}")
        return json_data.get("dataList", [])
    
    print("❌ Failed to fetch trades.")
    return []

# 🔍 Function to fetch open positions
def get_positions(wallet):
    url = f"{PERPS_API_BASE}/positions?walletAddress={wallet}"
    print(f"📡 Fetching positions from: {url}")
    response = requests.get(url)
    print(f"🔄 API Response Code: {response.status_code}")

    if response.status_code == 200:
        json_data = response.json()
        print(f"✅ Response Data:\n{json.dumps(json_data, indent=4)}")
        return json_data.get("dataList", [])
    
    print("❌ Failed to fetch positions.")
    return []

# 📌 Command: /start
@bot.message_handler(commands=["start"])
def start_message(message):
    welcome_text = ("🚀 Welcome to the Jupiter Perps Bot! 🔥\n\n"
                    "Use the following commands to track trades and positions:\n\n"
                    "📌 /trades <wallet_address> → Fetch last 5 trades\n"
                    "📌 /p <wallet_address> → Fetch all active positions\n"
                    "📌 /set <wallet_address> → Start tracking a wallet (Premium only)\n"
                    "📌 /unset <wallet_address> → Stop tracking a wallet")
    bot.reply_to(message, welcome_text)

# 📌 Command: /trades <wallet>
@bot.message_handler(commands=["trades"])
def send_trades(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Invalid command!\nPlease use: `/trades <wallet_address>`")
        return
    wallet = args[1]
    trades = get_trades(wallet)
    if not trades:
        bot.reply_to(message, "⚠ No trades found.")
        return
    
    response_text = "🟣 *𝗟𝗮𝘀𝘁 𝟱 𝗧𝗿𝗮𝗱𝗲𝘀*\n\n"
    for trade in trades[:5]:
        pnl = float(trade.get('pnl') or 0)
        pnl_text = f"🟢 *Profit:* ${pnl}" if pnl >= 0 else f"🔴 *Loss:* ${abs(pnl)}"
        
        size = float(trade.get("size", 0))
        collateral = abs(float(trade.get("collateralUsdDelta", 0)))  # FIXED: Collateral as Trade Amount
        leverage_value = round(size / collateral, 2) if collateral else "N/A"
        leverage_text = f"{leverage_value}x" if leverage_value != "N/A" else "N/A"
        
        response_text += (
            f"┌ 🔹 *Position:* {trade.get('positionName', 'N/A')}\n"
            f"├ 🔹 *Action:* {trade.get('action', 'N/A')}\n"
            f"├ 🔹 *Type:* {trade.get('side', 'N/A')}\n"
            f"├ 💰 *Entry Price:* ${trade.get('price', 'N/A')}\n"
            f"├ 📊 *Size:* {trade.get('size', 'N/A')}\n"
            f"├ 💵 *Trade Amount:* ${collateral}\n"  # FIXED
            f"├ ⚡ *Leverage:* {leverage_text}\n"
            f"└ {pnl_text}\n\n"
            f"🔗 [𝙑𝙞𝙚𝙬 𝙏𝙧𝙖𝙣𝙨𝙖𝙘𝙩𝙞𝙤𝙣](https://solscan.io/tx/{trade.get('txHash', '')})\n\n"
        )
    
    print(f"📌 Displaying last 5 trades for {wallet}")
    bot.send_message(message.chat.id, response_text, disable_web_page_preview=True)

# 📌 Command: /p <wallet>
@bot.message_handler(commands=["p"])
def fetch_positions(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Invalid command!\nPlease use: `/p <wallet_address>`")
        return
    wallet = args[1]
    positions = get_positions(wallet)
    
    if not positions:
        bot.reply_to(message, "⚠ No active positions.")
        return
    
    response_text = "🟢 *𝗔𝗰𝘁𝗶𝘃𝗲 𝗣𝗼𝘀𝗶𝘁𝗶𝗼𝗻𝘀*\n\n"
    
    for pos in positions:
        try:
            collateral = float(pos.get("collateral", 0))
            leverage = float(pos.get("leverage", 1))
            trade_amount = collateral * leverage  # Trade Amount Calculation
            
            created_time = datetime.utcfromtimestamp(pos.get("createdTime", 0)).strftime('%Y-%m-%d %H:%M:%S')
            pnl = float(pos.get('pnlAfterFeesUsd', 0))
            pnl_text = f"🟢 *Profit:* ${pnl}" if pnl >= 0 else f"🔴 *Loss:* ${abs(pnl)}"

            response_text += (
                f"┌ 🔹 *Position:* {pos.get('positionName', 'N/A')}\n"
                f"├ 🔹 *Side:* {pos.get('side', 'N/A')}\n"
                f"├ 💰 *Entry Price:* ${pos.get('entryPrice', 'N/A')}\n"
                f"├ 📊 *Size:* {pos.get('size', 'N/A')}\n"
                f"├ 💵 *Collateral:* ${collateral}\n"
                f"├ ⚡ *Leverage:* {leverage}x\n"
                f"├ 💰 *Trade Amount:* ${trade_amount:.2f}\n"
                f"├ 🔥 *Liquidation Price:* ${pos.get('liquidationPrice', 'N/A')}\n"
                f"├ ⏰ *Created Time:* {created_time}\n"
                f"└ {pnl_text}\n\n"
            )

        except Exception as e:
            print(f"❌ Error processing position: {e}")
    
    bot.send_message(message.chat.id, response_text, disable_web_page_preview=True)

# 📌 Command: /set <wallet>
@bot.message_handler(commands=["set"])
def set_tracking(message):
    bot.reply_to(message, "❌ This feature is only available for premium users.")

# 📌 Command: /unset <wallet>
@bot.message_handler(commands=["unset"])
def unset_tracking(message):
    bot.reply_to(message, "No Wallet Found! Say What?")

# 🔄 Start the bot
print("🤖 Bot is running...")
bot.polling()
