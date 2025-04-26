from flask import Flask, request
from openai import OpenAI
import os
import requests

# โหลดค่า Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# สร้าง OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# สร้าง Flask app
app = Flask(__name__)

# ฟังก์ชันส่งข้อความกลับไปที่ Messenger
def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v19.0/me/messages"
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "messaging_type": "RESPONSE",
    }
    params = {"access_token": PAGE_ACCESS_TOKEN}
    response = requests.post(url, headers=headers, params=params, json=payload)

    if response.status_code != 200:
        print(f"❌ ไม่สามารถส่งข้อความได้: {response.status_code} - {response.text}")
    else:
        print(f"✅ ส่งข้อความสำเร็จถึง {recipient_id}")

# ฟังก์ชันเรียก GPT มาตอบ
def ask_gpt(message_text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # หรือ gpt-4, gpt-3.5-turbo แล้วแต่ plan พี่โอ
            messages=[
                {"role": "system", "content": "คุณคือนักช่วยตอบข้อความลูกค้าบน Facebook อย่างสุภาพและกระชับ"},
                {"role": "user", "content": message_text}
            ],
            temperature=0.5,
            max_tokens=300,
        )
        reply = response.choices[0].message.content.strip()
        return reply
    except Exception as e:
        print(f"❌ GPT Error: {str(e)}")
        return "ขออภัย ระบบไม่สามารถตอบกลับได้ในขณะนี้"

# Endpoint สำหรับ Facebook Webhook (GET = Verify, POST = รับข้อความ)
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # สำหรับ Verify Token ตอนตั้ง Webhook
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook Verified!")
            return challenge, 200
        else:
            print("❌ Webhook Verification Failed")
            return "Verification token mismatch", 403

    elif request.method == "POST":
        # รับข้อความจาก Facebook
        data = request.get_json()
        print(f"📩 Webhook POST: {data}")

        if "object" in data and data["object"] == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event["sender"]["id"]
                    if "message" in messaging_event and "text" in messaging_event["message"]:
                        user_message = messaging_event["message"]["text"]

                        # ส่งข้อความที่ผู้ใช้พิมพ์ → ไปถาม GPT
                        bot_reply = ask_gpt(user_message)

                        # ส่งข้อความตอบกลับไปยัง Messenger
                        send_message(sender_id, bot_reply)

        return "ok", 200

# รัน app
if __name__ == "__main__":
    app.run(port=6969)
