import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application,MessageHandler,CommandHandler,filters


load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
print(f"TELEGRAM_BOT_TOKEN loaded successfully:", TELEGRAM_BOT_TOKEN)

async def start(update:Update,context):
    await update.message.reply_text(
        "Hi~ o(*￣▽￣*)ブ你好，我是NanoClaw。"
    )

async def echo(update:Update,context):
    await update.message.reply_text(
        update.message.text
    )

async def end(update:Update,context):
    await update.message.reply_text(
        "Bye~ o(*￣▽￣*)ブ再见，我是NanoClaw。"
    )

def main():
    app=Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    #注册处理器
    app.add_handler(CommandHandler("start",start))
    app.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,echo))
    app.add_handler(CommandHandler("end",end))

    print("Bot is running.....")
    app.run_polling()#轮询更新

if __name__ == "__main__":
    main()