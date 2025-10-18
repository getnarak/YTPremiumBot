from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FollowEvent,
    TemplateSendMessage, ButtonsTemplate, MessageAction
)
import random, re, os, logging

# =============================
# Flask App
# =============================
app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# =============================
# 🔧 LINE API TOKEN & SECRET
# =============================
CHANNEL_ACCESS_TOKEN = os.getenv(
    "LINE_CHANNEL_ACCESS_TOKEN",
    "I0ETW4qm2REynaRaPE7fCwNwA0wWoTmGrswAJE24QZo9gsFkJ1H6spxaQmGaw7fyv9NoN7/jKlJv8V/UgJTLUTc41lTlr5I5rkQx9lWBbv8+LSPt9iQilpM8OCJu47n9uWaglngSXeUzPDxM6S+eZQdB04t89/1O/w1cDnyilFU="
)
CHANNEL_SECRET = os.getenv(
    "LINE_CHANNEL_SECRET",
    "fa82b1e72ddeb8274847e7695ecd3872"
)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# =============================
# ระบบสถานะผู้ใช้
# =============================
user_state = {}

# =============================
# ข้อความต้อนรับ + แพ็กเกจ
# =============================
greeting_texts = [
    "🧁 สวัสดีค่า ยินดีต้อนรับสู่ร้าน YouTube Premium ราคาน่ารัก 💕",
    "🌈 ยินดีต้อนรับค้าบ~ มาดูแพ็กเกจน่ารัก ๆ ของเราได้เลย 💫",
    "☁️ สวัสดีค่ะ ขอบคุณที่แอดมาน้า~ พร้อมสมัคร YouTube Premium ราคาพิเศษมั้ยคะ 🍎"
]

package_prices = {
    "แพ็กเกจ 1 เดือน": "75.-",
    "แพ็กเกจ 3 เดือน": "225.-",
    "แพ็กเกจ 6 เดือน": "450.-",
    "แพ็กเกจ 12 เดือน": "900.-"
}

# =============================
# หน้าแรก
# =============================
@app.route("/")
def home():
    return "✅ LINE YouTube Premium Bot is running! 🎀"

# =============================
# Webhook Callback
# =============================
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    logging.info(f"📩 Incoming request: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logging.error("❌ Invalid signature. Body: %s", body)
        abort(400)
    except Exception as e:
        logging.error(f"⚠️ Error handling message: {e}")
        abort(500)
    return "OK"

# =============================
# ฟังก์ชันช่วยส่งข้อความ
# =============================
def safe_reply(reply_token, message):
    try:
        line_bot_api.reply_message(reply_token, message)
    except LineBotApiError as e:
        logging.error(f"❌ LINE API Error: {e}")

# =============================
# ฟังก์ชันแสดงเมนูแพ็กเกจ
# =============================
def send_package_menu(reply_token):
    template = ButtonsTemplate(
        title="🍓 เลือกแพ็กเกจ YouTube Premium 🍓",
        text="กดเลือกแพ็กเกจที่ต้องการได้เลย 💕",
        actions=[
            MessageAction(label="1 เดือน (75.-)", text="แพ็กเกจ 1 เดือน"),
            MessageAction(label="3 เดือน (225.-)", text="แพ็กเกจ 3 เดือน"),
            MessageAction(label="6 เดือน (450.-)", text="แพ็กเกจ 6 เดือน"),
            MessageAction(label="12 เดือน (900.-)", text="แพ็กเกจ 12 เดือน"),
        ]
    )
    safe_reply(reply_token, TemplateSendMessage(
        alt_text="เลือกแพ็กเกจ YouTube Premium 💖",
        template=template
    ))

# =============================
# เมื่อผู้ใช้แอดเพื่อน
# =============================
@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    user_state[user_id] = {"status": "greeted"}

    greeting = random.choice(greeting_texts)
    reply_text = (
        f"{greeting}\n\n"
        "พิมพ์ 'เลือกแพ็กเกจ' เพื่อดูเมนูแพ็กเกจ YouTube Premium ได้เลย 🍰"
    )
    safe_reply(event.reply_token, TextSendMessage(text=reply_text))

# =============================
# เมื่อผู้ใช้พิมพ์ข้อความ
# =============================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    logging.info(f"👤 {user_id} พิมพ์ข้อความ: {text}")

    info = user_state.setdefault(user_id, {"status": "greeted"})
    status = info.get("status", "greeted")

    # --- เมนูเริ่มต้น / แพ็กเกจ ---
    if text.lower() in ["เริ่ม", "เลือกแพ็กเกจ", "menu", "แพ็กเกจ", "เลือกแพ็กเกจใหม่"]:
        user_state[user_id] = {"status": "selecting_package"}
        send_package_menu(event.reply_token)
        return

    # --- เลือกแพ็กเกจ ---
    if text in package_prices:
        user_state[user_id].update({
            "status": "waiting_email",
            "package": text
        })
        reply = (
            "💌 ได้เลยค่า~ รบกวนพิมพ์อีเมลที่ต้องการใช้สมัคร YouTube Premium ด้วยนะคะ 🌷\n"
            "(หรือพิมพ์ 'เลือกแพ็กเกจ' เพื่อกลับไปดูเมนูอีกครั้งได้เลย 💕)"
        )
        safe_reply(event.reply_token, TextSendMessage(text=reply))
        return

    # --- ตรวจสอบอีเมล ---
    if status == "waiting_email":
        email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        if re.fullmatch(email_regex, text):
            package = user_state[user_id].get("package")
            price = package_prices.get(package, "-")

            reply = (
                f"🎉 ขอบคุณมากค่า~\n"
                f"📧 อีเมล: {text}\n"
                f"🎁 แพ็กเกจ: {package}\n"
                f"💸 ราคา: {price}\n\n"
                "⏳ แอดมินจะรีบตรวจสอบและติดต่อกลับไวที่สุดเลยนะคะ 💖"
            )

            # ✅ จบการทำงาน: เคลียร์สถานะผู้ใช้
            user_state.pop(user_id, None)

            safe_reply(event.reply_token, TextSendMessage(text=reply))
        else:
            safe_reply(event.reply_token, TextSendMessage(
                text="อีเมลไม่ถูกต้องค่ะ 😅 กรุณาพิมพ์อีเมลที่ถูกต้องอีกครั้งนะคะ"
            ))
        return

    # --- ข้อความอื่น (หลังจากจบการทำงานแล้ว) ---
    if status == "greeted":
        safe_reply(event.reply_token, TextSendMessage(
            text="😳 ขอโทษค่ะ ฉันไม่เข้าใจ พิมพ์ 'เลือกแพ็กเกจ' เพื่อดูเมนู YouTube Premium นะคะ 🍰"
        ))

# =============================
# รัน Flask Server
# =============================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    logging.info(f"🚀 Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)
