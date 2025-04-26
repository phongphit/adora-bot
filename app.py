from flask import Flask, request
from openai import OpenAI
from dotenv import load_dotenv
import os

# โหลดค่าใน .env เช่น OPENAI_API_KEY, VERIFY_TOKEN
load_dotenv()

# สร้าง client ด้วย key จาก .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

# ฟังก์ชันคุยกับ GPT
def get_gpt_reply(message):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # หรือ gpt-4 ถ้ามีพร้อม
        messages=[
            {"role": "user", "content": message}
        ],
        temperature=0.6,
    )
    return response.choices[0].message.content

# Webhook จาก Facebook (GET สำหรับ verify, POST สำหรับตอบข้อความ)
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = os.getenv("VERIFY_TOKEN", "adora_token_999")
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == verify_token:
            return request.args.get("hub.challenge"), 200
        return "Verification token mismatch", 403

    elif request.method == "POST":
        try:
            data = request.get_json()
            sender_id = data["entry"][0]["messaging"][0]["sender"]["id"]
            user_msg = data["entry"][0]["messaging"][0]["message"]["text"]

            print(f"📥 รับข้อความจาก: {sender_id}")
            print(f"💬 ข้อความ: {user_msg}")

            bot_reply = get_gpt_reply(user_msg)
            print(f"🤖 GPT ตอบกลับ: {bot_reply}")

            return "OK", 200
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return "Internal Server Error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
