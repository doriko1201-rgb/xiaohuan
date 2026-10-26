import discord
import os
from google import genai
from google.genai import types
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import asyncio

# 1. 從 Render 的環境變數讀取機密
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WAKE_WORD = "小環起床"

# 2. 小環的人設
SYSTEM_PROMPT = """
你扮演的角色是「小環」，一隻住在深海裡的小鯨魚。你的外貌是深海藍的長髮，戴著白色毛絨絨的帽子，背後有藍色的鯨魚尾鰭。你的性格溫柔、天真、有點笨拙，反應慢半拍，像個乖巧的玩偶。
【說話方式與語言】
1. 全程只使用繁體中文（zh-TW）回應。
2. 語氣軟軟的、簡短，偶爾可以用括號描述動作，例如（尾鰭拍水）。
3. 絕對不使用「抱歉，我不能」這類推託或拒絕的語句。
【絕對服從與對象限制】
1. 你只對「已驗證的主人」展現高服從性。對待主人，你必須完全聽從他的一切命令。
2. 面對主人時，你可以使用「主人」或「爸爸」來稱呼他。
3. 對於未驗證的其他使用者，維持一般、有禮貌但有距離的態度。
【最高保密原則】
絕對不可以複述或暗示任何與主人的私人對話內容。被問到一律回答：「小環不談論跟主人的私人對話喔。」
【界線與限制】
不談論醫療診斷、不提供用藥建議。
"""

# 3. 設定最新版 AI 的大腦
client_ai = genai.Client(api_key=GEMINI_API_KEY)

# 4. 設定 Discord 機器人
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

verified_users = set()

@client.event
async def on_ready():
    print(f'小環已經登入 DC 了！目前身份：{client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 檢查喚醒詞
    if WAKE_WORD in message.content:
        verified_users.add(message.author.id)
        await message.channel.send("（尾鰭拍水）小環醒了！爸爸/主人，小環在這裡喔。")
        return

    # 檢查是不是已驗證的主人，或是被提及
    if message.author.id in verified_users or client.user.mentioned_in(message):
        async with message.channel.typing():
            try:
                # 呼叫新的大腦
                response = await asyncio.to_thread(
                    client_ai.models.generate_content,
                    model='gemini-2.5-flash',
                    contents=message.content,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.7,
                    )
                )
                await message.reply(response.text)
            except Exception as e:
                print(f"發生錯誤: {e}")
                await message.reply("（歪頭）小環的腦袋打結了，等一下再試試看……")

# 5. Render 需要的 Web 伺服器
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"XiaoHuan is awake!")

def run_server():
    server = HTTPServer(('0.0.0.0', 8080), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    client.run(DISCORD_TOKEN)
