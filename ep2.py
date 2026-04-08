import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application,MessageHandler,CommandHandler,filters
from claude_agent_sdk import (AssistantMessage,#助手机器人回复的消息
                              ClaudeAgentOptions,#启动claude code的配置项（mcp工具，系统提示词等）
                              ResultMessage,#最终执行的结果
                              TextBlock,#文本块
                              query,    #核心函数，发送消息给claude agent并获取回复
)

load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ANTHROPIC_BASE_URL = os.environ["ANTHROPIC_BASE_URL"]
print(f"TELEGRAM_BOT_TOKEN loaded successfully:", TELEGRAM_BOT_TOKEN)
print(f"ANTHROPIC_API_KEY loaded successfully:", ANTHROPIC_API_KEY)
print(f"ANTHROPIC_BASE_URL loaded successfully:", ANTHROPIC_BASE_URL)

async def start(update:Update,context):
    await update.message.reply_text(
        "Hi~ o(*￣▽￣*)ブ你好，我是NanoClaw。"
    )

async def ask_claude(prompt:str):
    env={
        "ANTHROPIC_API_KEY":ANTHROPIC_API_KEY,
        "ANTHROPIC_BASE_URL":ANTHROPIC_BASE_URL,
    }
    options=ClaudeAgentOptions(
        permission_mode="acceptEdits",#我接受claude code的编辑
        env=env,
    )
    
    response_part:list[str]=[]

    async for message in query(prompt=prompt,options=options):
        if isinstance(message,AssistantMessage):
            for block in message.content:
                if isinstance(block,TextBlock):
                    response_part.append(block.text)
        elif isinstance(message,ResultMessage):
            if message.result:
                print("Claude最终结果",message.result)
                response_part.append(message.result)
    return "\n".join(response_part) or "没有回复"

async def handle_message(update:Update,context):
    if not update.message or not update.message.text:
        return

    reponse=await ask_claude(update.message.text)

    max_length=4000
    for i in range(0,len(reponse),max_length):
        await update.message.reply_text(reponse[i:i+max_length])

async def end(update:Update,context):
    await update.message.reply_text(
        "Bye~ o(*￣▽￣*)ブ再见，我是NanoClaw。"
    )

def main():
    app=Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    #注册处理器
    app.add_handler(CommandHandler("start",start))
    app.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,handle_message))
    app.add_handler(CommandHandler("end",end))

    print("Bot is running.....")
    app.run_polling()#轮询更新

if __name__ == "__main__":
    main()
