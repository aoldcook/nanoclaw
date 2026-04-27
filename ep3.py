import os
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application,MessageHandler,CommandHandler,filters
from claude_agent_sdk import (AssistantMessage,#助手机器人回复的消息
                              ClaudeAgentOptions,#启动claude code的配置项（mcp工具，系统提示词等）
                              PermissionResultAllow,#允许工具调用的权限结果
                              ResultMessage,#最终执行的结果
                              TextBlock,#文本块
                              query,    #核心函数，发送消息给claude agent并获取回复
                              create_sdk_mcp_server, tool, #创建mcp服务器
)

load_dotenv()
BASE_DIR=Path(__file__).resolve().parent#resolve()将路径转换为绝对路径，parent获取父目录
WORKSPACE_DIR=BASE_DIR/"workspace"
if not WORKSPACE_DIR.exists():
    WORKSPACE_DIR.mkdir(parents=True)

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

async def creat_mcp_sever_tools(bot,chat_id:int)->list:

    @tool("send_message","发送消息给用户",{"text":str})
    async def send_message(args):
        #这一行是主动给用户发消息
        await bot.send_message(chat_id=chat_id,text=args["text"])
        #返回值是告诉Agent发送消息的结果
        return{
            "content":[
                {
                    "type":"text",
                    "text":f"已向用户发送消息:{args['text']}"
                }
            ]
        }
    return [send_message]


async def allow_tool_use(tool_name, tool_input, context):
    # SDK expects a callable permission hook here, not a boolean flag.
    return PermissionResultAllow()

async def run_agent(prompt:str,bot,chat_id:int)->str:
    env={
        "ANTHROPIC_API_KEY":ANTHROPIC_API_KEY,
        "ANTHROPIC_BASE_URL":ANTHROPIC_BASE_URL,
    }
    
    #mcp服务器工具
    tools=await creat_mcp_sever_tools(bot,chat_id)
    
    options=ClaudeAgentOptions(
        cwd=str(WORKSPACE_DIR),#工作目录 - cwd 是 current working directory 的缩写
        allowed_tools=[
            "Read",#读取文件
            "Write",#写入文件
            "Edit",#编辑文件
            "Glob",#匹配文件
            "Grep",#搜索文件
        ],
        permission_mode="acceptEdits",#我接受claude code的编辑
        env=env,
        can_use_tool=allow_tool_use,
        mcp_servers={
            "assistant":create_sdk_mcp_server(
                name="assistant",
                tools=tools,
            ),
        },
    )
    
    response_part:list[str]=[]

    async def _make_prompt(text:str):
        "构造异步生成器prompt，解决SDK使用MCP时的兼容问题"
        yield{
            "type":"user",
            "message":{"role":"user","content":text}
        }

    async for message in query(prompt=_make_prompt(prompt),options=options):
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

    reponse=await run_agent(update.message.text,context.bot,update.effective_chat.id)

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
